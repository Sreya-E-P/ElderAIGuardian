import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useEmergencyStore = create(
  persist(
    (set, get) => ({
      activeEmergency: null,
      severity: null,
      emergencyId: null,
      emergencyHistory: [],
      panicMode: false,
      
      setActiveEmergency: (emergency) => {
        const isCritical = emergency?.severity === 'CRITICAL' || emergency?.severity === 'HIGH';
        set({ 
          activeEmergency: emergency,
          severity: emergency?.severity,
          emergencyId: emergency?.id,
          panicMode: isCritical
        });
        
        // Add to history
        if (emergency) {
          set((state) => ({
            emergencyHistory: [emergency, ...state.emergencyHistory].slice(0, 20)
          }));
        }
      },
      
      clearEmergency: () => {
        set({ 
          activeEmergency: null, 
          severity: null, 
          emergencyId: null,
          panicMode: false 
        });
      },
      
      togglePanicMode: () => {
        set((state) => ({ panicMode: !state.panicMode }));
      },
      
      setPanicMode: (enabled) => {
        set({ panicMode: enabled });
      },
      
      addToHistory: (emergency) => {
        set((state) => ({
          emergencyHistory: [emergency, ...state.emergencyHistory].slice(0, 20)
        }));
      },
      
      getPanicMode: () => {
        const state = get();
        return state.panicMode || (state.activeEmergency !== null && 
               (state.severity === 'CRITICAL' || state.severity === 'HIGH'));
      },
      
      getResponseStats: () => {
        const state = get();
        const resolved = state.emergencyHistory.filter(e => e.status === 'RESOLVED');
        const avgResponse = resolved.reduce((sum, e) => 
          sum + (e.response_time_seconds || 0), 0) / (resolved.length || 1);
        
        return {
          totalEmergencies: state.emergencyHistory.length,
          resolvedCount: resolved.length,
          avgResponseSeconds: Math.round(avgResponse),
          criticalIncidents: state.emergencyHistory.filter(e => e.severity === 'CRITICAL').length
        };
      }
    }),
    {
      name: 'emergency-storage',
      getStorage: () => localStorage,
    }
  )
);
