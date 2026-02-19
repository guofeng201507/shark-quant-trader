"""Broker Adapters for Live Trading - Phase 6

Based on Tech Design v1.2 Section 4.12.1
Implements FR-6.1: Broker API Integration
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from datetime import datetime
import uuid
import asyncio
import ssl
import certifi
import aiohttp

from .models import (
    LiveOrder,
    OrderResponse,
    AccountInfo,
    Position,
    OrderStatus
)


class BrokerAdapter(ABC):
    """Abstract broker adapter for multi-broker support.
    
    Based on PRD FR-6.1 requirements:
    - Account information query
    - Order submission (market, limit, stop)
    - Order status query
    - Real-time position updates via WebSocket
    """
    
    @property
    @abstractmethod
    def broker_name(self) -> str:
        """Return broker name"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to broker API"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker API"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> AccountInfo:
        """Get account balance, buying power, positions"""
        pass
    
    @abstractmethod
    async def submit_order(self, order: LiveOrder) -> OrderResponse:
        """Submit order to broker"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get status of submitted order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order"""
        pass
    
    @abstractmethod
    async def subscribe_positions(self, callback: Callable) -> None:
        """Subscribe to real-time position updates via WebSocket"""
        pass
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        return f"{self.broker_name.upper()}-{uuid.uuid4().hex[:12]}"


class AlpacaAdapter(BrokerAdapter):
    """Alpaca broker adapter for US ETFs.

    Supports REST API and WebSocket streaming.
    Paper trading by default for safety.
    """

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        paper: bool = True,
        demo_mode: bool = False,
        base_url: str = None
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.demo_mode = demo_mode
        self.base_url = base_url or ("https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets")
        self.ws_url = "wss://stream.data.alpaca.markets/v2/iex"
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection = None
        self._connected = False
    
    @property
    def broker_name(self) -> str:
        return "alpaca"
    
    async def connect(self) -> bool:
        """Connect to Alpaca API"""
        if self._connected:
            return True

        # Demo mode: skip actual API connection
        if self.demo_mode:
            self._connected = True
            return True

        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key
            }
            # Create SSL context with certifi certificates for macOS compatibility
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(headers=headers, connector=connector)
            # Test connection with account endpoint
            async with self.session.get(f"{self.base_url}/v2/account"):
                self._connected = True
                return True
        except Exception as e:
            print(f"Alpaca connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpaca API"""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False
        return True
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information from Alpaca"""
        if not self._connected:
            await self.connect()

        # Demo mode: return simulated account
        if self.demo_mode:
            return AccountInfo(
                account_id="demo-alpaca-account",
                cash=50000.0,
                buying_power=100000.0,
                portfolio_value=100000.0,
                positions={},
                timestamp=datetime.now()
            )

        try:
            async with self.session.get(f"{self.base_url}/v2/account") as resp:
                data = await resp.json()
            
            # Get positions
            positions = {}
            async with self.session.get(f"{self.base_url}/v2/positions") as resp:
                if resp.status == 200:
                    pos_list = await resp.json()
                    for p in pos_list:
                        symbol = p.get("symbol")
                        positions[symbol] = Position(
                            symbol=symbol,
                            quantity=float(p.get("qty", 0)),
                            avg_cost=float(p.get("avg_entry_price", 0)),
                            current_price=float(p.get("current_price", 0)),
                            market_value=float(p.get("market_value", 0)),
                            unrealized_pnl=float(p.get("unrealized_pl", 0))
                        )
            
            return AccountInfo(
                account_id=data.get("id", ""),
                cash=float(data.get("cash", 0)),
                buying_power=float(data.get("buying_power", 0)),
                portfolio_value=float(data.get("portfolio_value", 0)),
                positions=positions,
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Alpaca get_account_info error: {e}")
            raise
    
    async def submit_order(self, order: LiveOrder) -> OrderResponse:
        """Submit order to Alpaca"""
        if not self._connected:
            await self.connect()

        # Demo mode: simulate order submission
        if self.demo_mode:
            return OrderResponse(
                broker_order_id=self._generate_order_id(),
                status="FILLED",
                message="Demo order filled",
                timestamp=datetime.now()
            )

        payload = {
            "symbol": order.symbol,
            "qty": str(order.quantity),
            "side": order.side.lower(),
            "type": order.order_type.lower(),
            "time_in_force": "day"
        }
        if order.limit_price:
            payload["limit_price"] = str(order.limit_price)
        if order.stop_price:
            payload["stop_price"] = str(order.stop_price)
        
        try:
            async with self.session.post(
                f"{self.base_url}/v2/orders",
                json=payload
            ) as resp:
                data = await resp.json()
                return OrderResponse(
                    broker_order_id=data.get("id", ""),
                    status=data.get("status", "SUBMITTED"),
                    message=data.get("message", ""),
                    timestamp=datetime.now()
                )
        except Exception as e:
            print(f"Alpaca submit_order error: {e}")
            raise
    
    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get order status from Alpaca"""
        if not self._connected:
            await self.connect()
        
        # Demo mode
        if not self.api_key:
            return OrderResponse(
                broker_order_id=order_id,
                status="FILLED",
                message="Demo order",
                timestamp=datetime.now()
            )
        
        try:
            async with self.session.get(f"{self.base_url}/v2/orders/{order_id}") as resp:
                data = await resp.json()
                return OrderResponse(
                    broker_order_id=data.get("id", ""),
                    status=data.get("status", "UNKNOWN"),
                    message=data.get("message", ""),
                    timestamp=datetime.now()
                )
        except Exception as e:
            print(f"Alpaca get_order_status error: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Alpaca"""
        if not self._connected:
            await self.connect()
        
        # Demo mode
        if not self.api_key:
            return True
        
        try:
            async with self.session.delete(f"{self.base_url}/v2/orders/{order_id}"):
                return True
        except Exception:
            return False
    
    async def subscribe_positions(self, callback: Callable) -> None:
        """Subscribe to position updates via WebSocket"""
        # WebSocket implementation would go here
        # For demo, we'll skip actual WebSocket connection
        pass


class BinanceAdapter(BrokerAdapter):
    """Binance adapter for cryptocurrency trading.

    Supports spot and futures markets.
    Testnet mode available for safe testing.
    """

    def __init__(
        self,
        api_key: str = "",
        secret_key: str = "",
        testnet: bool = True,
        demo_mode: bool = False,
        base_url: str = None
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.demo_mode = demo_mode
        self.base_url = base_url or ("https://testnet.binance.vision" if testnet else "https://api.binance.com")
        self.futures_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self._connected = False
    
    @property
    def broker_name(self) -> str:
        return "binance"
    
    async def connect(self) -> bool:
        """Connect to Binance API"""
        if self._connected:
            return True

        # Demo mode: skip actual API connection
        if self.demo_mode:
            self._connected = True
            return True

        try:
            self.session = aiohttp.ClientSession()
            # Test connection with ping
            async with self.session.get(f"{self.base_url}/api/v3/ping"):
                self._connected = True
                return True
        except Exception as e:
            print(f"Binance connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance API"""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False
        return True
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information from Binance"""
        if not self._connected:
            await self.connect()

        # Demo mode
        if self.demo_mode:
            return AccountInfo(
                account_id="demo-binance-account",
                cash=50000.0,
                buying_power=100000.0,
                portfolio_value=100000.0,
                positions={},
                timestamp=datetime.now()
            )

        try:
            # Get spot account info
            async with self.session.get(f"{self.base_url}/api/v3/account") as resp:
                data = await resp.json()
            
            positions = {}
            for balance in data.get("balances", []):
                free = float(balance.get("free", 0))
                locked = float(balance.get("locked", 0))
                if free + locked > 0:
                    symbol = balance.get("asset")
                    # Get current price
                    try:
                        async with self.session.get(
                            f"{self.base_url}/api/v3/ticker/price",
                            params={"symbol": f"{symbol}USDT"}
                        ) as price_resp:
                            price_data = await price_resp.json()
                            current_price = float(price_data.get("price", 0))
                    except:
                        current_price = 0
                    
                    positions[symbol] = Position(
                        symbol=symbol,
                        quantity=free + locked,
                        avg_cost=0,
                        current_price=current_price,
                        market_value=(free + locked) * current_price
                    )
            
            return AccountInfo(
                account_id=data.get("accountType", "SPOT"),
                cash=float(data.get("buyerCommission", 0)),
                buying_power=100000.0,  # Calculate from balances
                portfolio_value=sum(p.market_value for p in positions.values()),
                positions=positions,
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Binance get_account_info error: {e}")
            raise
    
    async def submit_order(self, order: LiveOrder) -> OrderResponse:
        """Submit order to Binance"""
        if not self._connected:
            await self.connect()

        # Demo mode
        if self.demo_mode:
            return OrderResponse(
                broker_order_id=self._generate_order_id(),
                status="FILLED",
                message="Demo order filled",
                timestamp=datetime.now()
            )

        # Map order side
        side = order.side.upper()
        
        # Build endpoint
        if order.order_type == "MARKET":
            endpoint = "/api/v3/order"
            params = {
                "symbol": order.symbol,
                "side": side,
                "type": "MARKET",
                "quantity": order.quantity
            }
        else:
            endpoint = "/api/v3/order"
            params = {
                "symbol": order.symbol,
                "side": side,
                "type": "LIMIT",
                "quantity": order.quantity,
                "price": order.limit_price,
                "timeInForce": "GTC"
            }
        
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                params=params
            ) as resp:
                data = await resp.json()
                return OrderResponse(
                    broker_order_id=data.get("orderId", ""),
                    status=data.get("status", "FILLED"),
                    message=data.get("msg", ""),
                    timestamp=datetime.now()
                )
        except Exception as e:
            print(f"Binance submit_order error: {e}")
            raise
    
    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get order status from Binance"""
        # Demo mode
        if not self.api_key:
            return OrderResponse(
                broker_order_id=order_id,
                status="FILLED",
                message="Demo order",
                timestamp=datetime.now()
            )
        
        # Would implement query order endpoint
        return OrderResponse(
            broker_order_id=order_id,
            status="UNKNOWN",
            message="Not implemented",
            timestamp=datetime.now()
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on Binance"""
        # Demo mode
        if not self.api_key:
            return True
        
        try:
            async with self.session.delete(f"{self.base_url}/api/v3/order"):
                return True
        except Exception:
            return False
    
    async def subscribe_positions(self, callback: Callable) -> None:
        """Subscribe to position updates via WebSocket"""
        # WebSocket implementation would go here
        pass


class IBKRAdapter(BrokerAdapter):
    """Interactive Brokers adapter for global markets.
    
    Uses TWS API via ib_insync library.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497):
        self.host = host
        self.port = port
        self.ib = None  # ib_insync.IB instance
        self._connected = False
    
    @property
    def broker_name(self) -> str:
        return "ibkr"
    
    async def connect(self) -> bool:
        """Connect to TWS/Gateway"""
        # In production, would use ib_insync
        # For demo, simulate connection
        if not self._connected:
            # Try to import and connect
            try:
                from ib_insync import IB
                self.ib = IB()
                await asyncio.sleep(0.1)  # Simulate connection time
                self._connected = True
            except ImportError:
                print("ib_insync not installed - using demo mode")
                self._connected = True
        return True
    
    async def disconnect(self) -> bool:
        """Disconnect from TWS"""
        if self.ib:
            self.ib.disconnect()
        self._connected = False
        return True
    
    async def get_account_info(self) -> AccountInfo:
        """Get account information from IB"""
        # Demo mode
        return AccountInfo(
            account_id="demo-ibkr-account",
            cash=50000.0,
            buying_power=100000.0,
            portfolio_value=100000.0,
            positions={},
            timestamp=datetime.now()
        )
    
    async def submit_order(self, order: LiveOrder) -> OrderResponse:
        """Submit order to IB"""
        # Demo mode
        return OrderResponse(
            broker_order_id=self._generate_order_id(),
            status="FILLED",
            message="Demo order filled",
            timestamp=datetime.now()
        )
    
    async def get_order_status(self, order_id: str) -> OrderResponse:
        """Get order status from IB"""
        return OrderResponse(
            broker_order_id=order_id,
            status="FILLED",
            message="Demo order",
            timestamp=datetime.now()
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel order on IB"""
        return True
    
    async def subscribe_positions(self, callback: Callable) -> None:
        """Subscribe to position updates"""
        pass


class BrokerFactory:
    """Factory for creating broker adapters"""
    
    @staticmethod
    def create_broker(
        broker_type: str,
        **kwargs
    ) -> BrokerAdapter:
        """Create a broker adapter instance"""
        brokers = {
            "alpaca": AlpacaAdapter,
            "binance": BinanceAdapter,
            "ibkr": IBKRAdapter
        }
        
        if broker_type.lower() not in brokers:
            raise ValueError(f"Unknown broker type: {broker_type}")
        
        return brokers[broker_type.lower()](**kwargs)
    
    @staticmethod
    def get_default_brokers(
        alpaca_paper: bool = True,
        binance_testnet: bool = True
    ) -> Dict[str, BrokerAdapter]:
        """Get default broker set"""
        return {
            "alpaca": AlpacaAdapter(paper=alpaca_paper),
            "binance": BinanceAdapter(testnet=binance_testnet),
            "ibkr": IBKRAdapter()
        }
