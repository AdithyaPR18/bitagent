import { useEffect, useRef, useState, useCallback } from "react";
import type { WSMessage } from "../types";

export function useWebSocket(onMessage?: (msg: WSMessage) => void) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const cbRef = useRef(onMessage);
  cbRef.current = onMessage;

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };
    ws.onmessage = (e) => {
      try {
        cbRef.current?.(JSON.parse(e.data));
      } catch {}
    };
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { connected };
}
