export function createDriverStore(initialState = {}) {
  const defaultState = {
    symbol: 'NQ',
    quantity: 1,
    tpTicks: 120,
    slTicks: 40,
    tpEnabled: true,
    slEnabled: true,
    tickSize: 0.25,
    entryPrice: null,
    lastSource: 'init',
    lastUpdated: Date.now(),
  };

  let state = { ...defaultState, ...initialState };
  const listeners = new Set();

  function notify() {
    for (const listener of listeners) {
      try {
        listener({ ...state });
      } catch (err) {
        console.warn('[DriverStore] listener error', err);
      }
    }
  }

  function getState() {
    return { ...state };
  }

  function applyUpdate(patch = {}, source = 'unknown') {
    const nextState = { ...state, ...patch, lastSource: source, lastUpdated: Date.now() };
    const changed = Object.keys(nextState).some((key) => nextState[key] !== state[key]);
    if (!changed) {
      return state;
    }
    state = nextState;
    notify();
    return state;
  }

  function subscribe(listener) {
    listeners.add(listener);
    listener({ ...state });
    return () => listeners.delete(listener);
  }

  return { getState, applyUpdate, subscribe };
}

if (typeof window !== 'undefined') {
  if (!window.TradoAutoState) {
    window.TradoAutoState = createDriverStore();
  }
}
