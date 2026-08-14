from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(
    prefix="/api/v1/realtime",
    tags=["Realtime"],
)


connected_clients: set[WebSocket] = set()


@router.websocket("/ws")
async def realtime_ws(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Campus Sentinel realtime connected",
        })

        while True:
            message = await websocket.receive_text()

            for client in list(connected_clients):
                try:
                    await client.send_json({
                        "type": "update",
                        "message": message,
                    })
                except Exception:
                    connected_clients.discard(client)

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    finally:
        connected_clients.discard(websocket)
