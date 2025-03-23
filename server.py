import asyncio
import os
from mcp.server.fastmcp import FastMCP
from pycoingecko.api import CoinGeckoAPI

# Initialize the CoinGecko API client
cg = CoinGeckoAPI(api_key=os.getenv("COINGECKO_API_KEY"))

# Create our MCP server
app = FastMCP("coingecko-mcp-server")

# ---------- PING ----------#
@app.tool()
async def ping() -> dict:
    """Check API server status"""
    try:
        result = cg.ping()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------- KEY ----------#
# @app.tool()
# async def key() -> dict:
#     """Monitor your account's API usage, including rate limits, monthly total credits, remaining credits, and more"""
#     try:
#         result = cg.key()
#         return {"success": True, "data": result}
#     except Exception as e:
#         return {"success": False, "error": str(e)}

# ---------- SIMPLE ----------#
@app.tool()
async def get_price(ids: str, vs_currencies: str) -> dict:
    """Get the current price of any cryptocurrencies in any other supported currencies that you need.
    
    Args:
        ids: The ids of the cryptocurrencies to get prices for (comma-separated)
        vs_currencies: The target currencies to get prices in (comma-separated)
    """
    try:
        result = cg.get_price(ids=ids, vs_currencies=vs_currencies)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_token_price(id: str, contract_addresses: str, vs_currencies: str) -> dict:
    """Get the current price of any tokens on this coin (ETH only at this stage) in any other supported currencies.
    
    Args:
        id: The platform id (e.g., ethereum)
        contract_addresses: The token contract addresses (comma-separated)
        vs_currencies: The target currencies to get prices in (comma-separated)
    """
    try:
        result = cg.get_token_price(id=id, contract_addresses=contract_addresses, vs_currencies=vs_currencies)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_supported_vs_currencies() -> dict:
    """Get list of supported_vs_currencies"""
    try:
        result = cg.get_supported_vs_currencies()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------- COINS ----------#
@app.tool()
async def get_coins(
    vs_currency: str = "usd",
    order: str = "market_cap_desc",
    per_page: int = 10,
    page: int = 1,
    sparkline: bool = False
) -> dict:
    """List all supported coins with detailed information.
    
    Args:
        vs_currency: The target currency of market data (usd, eur, jpy, etc.)
        order: Sort results by: market_cap_desc, market_cap_asc, volume_desc, volume_asc, id_desc, id_asc
        per_page: Number of results per page (1-250)
        page: Page number
        sparkline: Include sparkline 7 days data
    """
    try:
        result = cg.get_coins_markets(
            vs_currency=vs_currency,
            order=order,
            per_page=per_page,
            page=page,
            sparkline=sparkline
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_coin_by_id(id: str, localization: bool = True, tickers: bool = True, 
                        market_data: bool = True, community_data: bool = True, 
                        developer_data: bool = True, sparkline: bool = False) -> dict:
    """Get current data (name, price, market, etc.) for a coin.
    
    Args:
        id: The coin id (e.g. bitcoin)
        localization: Include all localized languages in response
        tickers: Include ticker data
        market_data: Include market data
        community_data: Include community data
        developer_data: Include developer data
        sparkline: Include sparkline 7 days data
    """
    try:
        result = cg.get_coin_by_id(
            id=id,
            localization=localization,
            tickers=tickers,
            market_data=market_data,
            community_data=community_data,
            developer_data=developer_data,
            sparkline=sparkline
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_coin_market_chart_by_id(id: str, vs_currency: str, days: str) -> dict:
    """Get historical market data include price, market cap, and 24h volume.
    
    Args:
        id: The coin id (e.g. bitcoin)
        vs_currency: The target currency of market data (usd, eur, jpy, etc.)
        days: Data up to number of days ago (1/7/14/30/90/180/365/max)
    """
    try:
        result = cg.get_coin_market_chart_by_id(id=id, vs_currency=vs_currency, days=days)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_coin_market_chart_range_by_id(
    id: str, vs_currency: str, from_timestamp: int, to_timestamp: int
) -> dict:
    """Get historical market data include price, market cap, and 24h volume within a range of timestamp.
    
    Args:
        id: The coin id (e.g. bitcoin)
        vs_currency: The target currency of market data (usd, eur, jpy, etc.)
        from_timestamp: From date in UNIX Timestamp (eg. 1392577232)
        to_timestamp: To date in UNIX Timestamp (eg. 1422577232)
    """
    try:
        result = cg.get_coin_market_chart_range_by_id(
            id=id,
            vs_currency=vs_currency,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------- EXCHANGES ----------#
@app.tool()
async def get_exchanges(per_page: int = 100, page: int = 1) -> dict:
    """List all exchanges.
    
    Args:
        per_page: Number of results per page
        page: Page number
    """
    try:
        result = cg.get_exchanges_list(per_page=per_page, page=page)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_exchange_by_id(id: str) -> dict:
    """Get exchange volume in BTC and tickers.
    
    Args:
        id: The exchange id (e.g. binance)
    """
    try:
        result = cg.get_exchanges_by_id(id=id)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------- GLOBAL ----------#
@app.tool()
async def get_global() -> dict:
    """Get cryptocurrency global data"""
    try:
        result = cg.get_global()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.tool()
async def get_global_defi() -> dict:
    """Get cryptocurrency global decentralized finance(defi) data"""
    try:
        result = cg.get_global_decentralized_finance_defi()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------- TRENDING ----------#
@app.tool()
async def get_trending() -> dict:
    """Get trending search coins (Top-7) on CoinGecko in the last 24 hours"""
    try:
        result = cg.get_search_trending()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ---------- SEARCH ----------#
@app.tool()
async def search(query: str) -> dict:
    """Search for coins, categories and markets on CoinGecko.
    
    Args:
        query: Search string
    """
    try:
        result = cg.search(query=query)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("Server Started!")
    print("Ping:", cg.ping())
    app.run()
