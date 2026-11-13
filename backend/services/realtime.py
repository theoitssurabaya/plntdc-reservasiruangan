"""
Real-Time Event Engine & WebSocket Dispatcher
Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)

Menyediakan pub-sub broadcast event berbasis WebSocket untuk sinkronisasi live
secara dua arah antara pengguna publik dan Dashboard Admin.
Mendukung eksekusi asinkron murni maupun pemanggilan dari worker thread sinkron.
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("tdc.realtime")
logger.setLevel(logging.INFO)


class RealtimeManager:
    """Mengelola koneksi WebSocket aktif dan melakukan broadcast event ke seluruh client."""

    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self._lock: Optional[asyncio.Lock] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Menyimpan referensi ke main asyncio event loop untuk thread-safe dispatch."""
        self._loop = loop
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Menerima dan mendaftarkan koneksi WebSocket baru."""
        await websocket.accept()
        if self._lock:
            async with self._lock:
                self.active_connections.add(websocket)
        else:
            self.active_connections.add(websocket)
        
        # Kirim sinyal selamat datang untuk konfirmasi konektivitas
        try:
            await websocket.send_text(
                json.dumps({
                    "event": "connected",
                    "data": {
                        "status": True,
                        "message": "Sistem Real-Time PLN TDC Aktif & Terhubung",
                        "total_clients": len(self.active_connections)
                    }
                })
            )
        except Exception:
            pass
        logger.info(f"[RealTime] Client baru terhubung. Total klien aktif: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Menghapus koneksi WebSocket yang ditutup."""
        if self._lock:
            async with self._lock:
                self.active_connections.discard(websocket)
        else:
            self.active_connections.discard(websocket)
        logger.info(f"[RealTime] Client terputus. Sisa klien aktif: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Mengirimkan pesan event JSON ke semua koneksi WebSocket aktif."""
        if not self.active_connections:
            return

        payload = json.dumps({
            "event": event_type,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        })

        dead_connections: Set[WebSocket] = set()
        connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.add(connection)

        if dead_connections:
            if self._lock:
                async with self._lock:
                    for dead in dead_connections:
                        self.active_connections.discard(dead)
            else:
                for dead in dead_connections:
                    self.active_connections.discard(dead)

    def broadcast_sync(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Fungsi pembungkus thread-safe untuk memanggil broadcast dari worker sinkron."""
        target_loop = self._loop
        if target_loop is None:
            try:
                target_loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        if target_loop and target_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(event_type, data), target_loop)
        else:
            try:
                asyncio.run(self.broadcast(event_type, data))
            except Exception as ex:
                logger.warning(f"[RealTime] Gagal broadcast sinkron: {ex}")

    def get_client_count(self) -> int:
        """Mengembalikan jumlah client yang sedang aktif terhubung."""
        return len(self.active_connections)


# Singleton Instance
realtime_manager = RealtimeManager()


def broadcast_event(event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Utilitas global untuk memicu pembaruan real-time di seluruh sistem."""
    try:
        # Coba eksekusi langsung jika berada di event loop yang sama
        loop = asyncio.get_running_loop()
        loop.create_task(realtime_manager.broadcast(event_type, data))
    except RuntimeError:
        # Panggil versi threadsafe jika dipanggil dari sync function / threadpool
        realtime_manager.broadcast_sync(event_type, data)

