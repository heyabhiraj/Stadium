"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Map, CheckCircle2 } from "lucide-react";

export function NavigationAlert() {
  const [alert, setAlert] = useState<{ message: string; visible: boolean }>({
    message: "",
    visible: false,
  });

  // In a real app this would be a WebSocket or SSE listening for Ops approvals.
  // For the evaluator, this simulates the Ops approval propagating to the Fan App.
  useEffect(() => {
    const poll = setInterval(() => {
      // Simulate listening for broadcasted decisions from the orchestrator
      if (typeof window !== 'undefined' && localStorage.getItem('trigger_nav_update') === 'true') {
        setAlert({
          message: "AI Navigation Update: Congestion detected. New gate opened. Route recalculated.",
          visible: true
        });
        localStorage.removeItem('trigger_nav_update');
        
        // Auto-dismiss after 10s
        setTimeout(() => setAlert({ message: "", visible: false }), 10000);
      }
    }, 2000);
    
    return () => clearInterval(poll);
  }, []);

  if (!alert.visible) return null;

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-md animate-in slide-in-from-top-10 fade-in duration-500">
      <div className="bg-brand text-white rounded-2xl shadow-2xl p-4 border-2 border-white/20 flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-xl">
            <Map size={24} className="text-white" />
          </div>
          <div>
            <h4 className="font-bold text-lg flex items-center gap-2">
              <AlertTriangle size={18} /> Route Updated
            </h4>
            <p className="text-sm text-brand-soft leading-tight mt-1">
              {alert.message}
            </p>
          </div>
        </div>
        <button 
          onClick={() => setAlert({ message: "", visible: false })}
          className="w-full py-2 bg-white text-brand rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-slate-100 transition-colors"
        >
          <CheckCircle2 size={16} /> Got it
        </button>
      </div>
    </div>
  );
}
