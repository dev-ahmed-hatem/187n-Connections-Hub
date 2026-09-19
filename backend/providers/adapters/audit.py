"""Read-only audit probes. A sample proves API readability, not report completeness."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import json
import re


def period(params):
    try:
        start = date.fromisoformat(params['start_date'])
        end = date.fromisoformat(params['end_date'])
    except (KeyError, ValueError, TypeError):
        raise ValueError('Explicit start_date and end_date (YYYY-MM-DD) are required.')
    if start > end or end >= date.today():
        raise ValueError('Use a completed period ending before today.')
    return {'start_date': start.isoformat(), 'end_date': end.isoformat()}


def identifier(value, pattern):
    if not re.fullmatch(pattern, str(value or '')):
        raise ValueError('Invalid account identifier.')
    return str(value)


def result(provider, account, dates, currency, timezone, rows, **extra):
    if not currency or not timezone:
        raise ValueError('Account currency and time zone are required.')
    return dict(provider=provider, resource='audit', account_id=account, period=dates,
                currency=currency, timezone=timezone, rows=rows, mock=False,
                sample=True, **extra)


def google(adapter, token, params, meta, analytics=False):
    dates = period(params)
    headers = {'Authorization': f'Bearer {token}'}
    if analytics:
        pid = identifier(params.get('property_id'), r'[0-9]+')
        account = f'properties/{pid}'
        info = adapter._get(f'https://analyticsadmin.googleapis.com/v1beta/{account}', headers=headers)
        if info.get('name') != account:
            raise ValueError('GA4 property identity mismatch.')
        base = {'dateRanges': [{'startDate': dates['start_date'], 'endDate': dates['end_date']}], 'limit': 100}
        endpoint = f'https://analyticsdata.googleapis.com/v1beta/{account}:runReport'
        traffic = adapter._post(endpoint, headers=headers, json={**base,
            'dimensions': [{'name': 'date'}, {'name': 'sessionDefaultChannelGroup'}],
            'metrics': [{'name': n} for n in ['sessions', 'activeUsers', 'ecommercePurchases', 'purchaseRevenue', 'keyEvents']]})
        events = adapter._post(endpoint, headers=headers, json={**base,
            'dimensions': [{'name': 'eventName'}],
            'metrics': [{'name': 'eventCount'}, {'name': 'keyEvents'}],
            'dimensionFilter': {'filter': {'fieldName': 'eventName', 'inListFilter': {
                'values': ['view_item', 'add_to_cart', 'begin_checkout', 'purchase', 'refund']}}}})
        return result('ga4', account, dates, info.get('currencyCode'), info.get('timeZone'),
                      traffic.get('rows', []), events=events.get('rows', []),
                      truncated=traffic.get('rowCount', 0) > 100 or events.get('rowCount', 0) > 100)
    cid = identifier(meta.get('external_account_id', '').replace('-', ''), r'[0-9]{10}')
    login = meta.get('login_customer_id') or adapter.config.get('login_customer_id')
    if login:
        headers['login-customer-id'] = identifier(str(login).replace('-', ''), r'[0-9]{10}')
    # Since 2026-09-09 access levels belong to the OAuth Cloud project.
    endpoint = f'https://googleads.googleapis.com/{adapter.config.get("api_version", "v24")}/customers/{cid}/googleAds:search'
    info = adapter._post(endpoint, headers=headers, json={'query':
        'SELECT customer.id, customer.currency_code, customer.time_zone FROM customer'})
    account = (info.get('results') or [{}])[0].get('customer', {})
    if str(account.get('id')) != cid:
        raise ValueError('Google Ads customer identity mismatch.')
    query = ('SELECT campaign.id, campaign.name, campaign.status, metrics.cost_micros, '
             'metrics.impressions, metrics.clicks, metrics.conversions, metrics.conversions_value '
             f"FROM campaign WHERE segments.date BETWEEN '{dates['start_date']}' AND '{dates['end_date']}' LIMIT 100")
    report = adapter._post(endpoint, headers=headers, json={'query': query})
    return result('google-ads', cid, dates, account.get('currencyCode'), account.get('timeZone'),
                  report.get('results', []), truncated=bool(report.get('nextPageToken')),
                  attribution='Google Ads configured conversion actions; cost is in micros')


def meta_ads(adapter, token, params, meta):
    dates = period(params)
    aid = identifier(meta.get('external_account_id'), r'act_[0-9]+')
    headers = {'Authorization': f'Bearer {token}'}
    info = adapter._get(f'{adapter.graph}/{aid}', headers=headers,
                        params={'fields': 'id,account_id,currency,timezone_name,business'})
    if info.get('id') != aid:
        raise ValueError('Meta ad account identity mismatch.')
    expected_business = identifier(params.get('business_id'), r'[0-9]+')
    if str(info.get('business', {}).get('id')) != expected_business:
        raise ValueError('Meta business identity mismatch or unavailable; verify asset ownership.')
    report = adapter._get(f'{adapter.graph}/{aid}/insights', headers=headers, params={
        'fields': 'account_id,campaign_id,campaign_name,spend,impressions,clicks,actions,action_values',
        'level': 'campaign', 'limit': 100,
        'time_range': json.dumps({'since': dates['start_date'], 'until': dates['end_date']}),
        'use_unified_attribution_setting': 'true', 'action_report_time': 'conversion'})
    return result('meta-ads', aid, dates, info.get('currency'), info.get('timezone_name'),
                  report.get('data', []), business_id=expected_business,
                  truncated=bool(report.get('paging', {}).get('next')),
                  attribution='Ad-set attribution settings; actions reported on conversion date')


def shopify(adapter, token, params, meta):
    dates = period(params)
    shop = identifier(meta.get('external_account_id'), r'[a-z0-9][a-z0-9-]*\.myshopify\.com')
    headers = {'X-Shopify-Access-Token': token}
    url = f'https://{shop}/admin/api/{adapter.config.get("api_version", "2026-07")}/graphql.json'
    metadata = adapter._post(url, headers=headers, json={'query': '''query AuditShop {
      shop { myshopifyDomain currencyCode ianaTimezone }
      currentAppInstallation { accessScopes { handle } }
    }'''})
    if metadata.get('errors'):
        raise ValueError('Shopify account metadata request failed.')
    data = metadata.get('data') or {}
    info = data.get('shop') or {}
    if info.get('myshopifyDomain') != shop:
        raise ValueError('Shopify shop identity mismatch.')
    tz = ZoneInfo(info['ianaTimezone'])
    start = datetime.combine(date.fromisoformat(dates['start_date']), time.min, tz).isoformat()
    end = datetime.combine(date.fromisoformat(dates['end_date']) + timedelta(days=1), time.min, tz).isoformat()
    scopes = [s['handle'] for s in data.get('currentAppInstallation', {}).get('accessScopes', [])]
    if not {'read_orders', 'write_orders'}.intersection(scopes):
        raise ValueError('Shopify orders permission missing.')
    if (date.today() - date.fromisoformat(dates['start_date'])).days >= 60 and 'read_all_orders' not in scopes:
        raise ValueError('Older orders require approved read_all_orders access.')
    query = '''query AuditOrders($query: String!) {
      orders(first: 50, query: $query, sortKey: CREATED_AT) {
        pageInfo { hasNextPage }
        nodes { id createdAt currencyCode
          totalPriceSet { shopMoney { amount currencyCode } }
          totalRefundedSet { shopMoney { amount currencyCode } }
          refunds { id createdAt totalRefundedSet { shopMoney { amount currencyCode } } }
        }
      }
    }'''
    report = adapter._post(url, headers=headers, json={'query': query, 'variables': {
        'query': f"created_at:>='{start}' created_at:<'{end}'"}})
    if report.get('errors'):
        raise ValueError('Shopify GraphQL audit query failed; verify app permissions.')
    orders = (report.get('data') or {}).get('orders') or {}
    return result('shopify', shop, dates, info.get('currencyCode'), info.get('ianaTimezone'),
                  orders.get('nodes', []), scopes=scopes,
                  truncated=bool(orders.get('pageInfo', {}).get('hasNextPage')),
                  refunds_basis='Refunds of orders created in the selected period, including refunds made later; not a refund-date ledger.',
                  funnel='Storefront session funnel unavailable in this orders query; validate GA4 events separately.')
