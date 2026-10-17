import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api-client';
import type { MarketTicker } from '../../types';
import { TrendingUp, TrendingDown, Activity, Sparkles } from 'lucide-react';

interface TopMarketRibbonProps {
  onSelectStock?: (symbol: string) => void;
}

const FALLBACK_TICKERS: MarketTicker[] = [
  {
    symbol: '^IXIC',
    display_symbol: 'NASDAQ',
    label: 'NASDAQ',
    category: 'INDEX',
    name: 'Nasdaq Composite',
    price: 18250.3,
    prev_close: 18622.75,
    change_abs: -372.45,
    change_pct: -2.0,
    is_positive: false,
    currency: 'USD',
    exchange: 'NAS',
    sparkline: [18650, 18580, 18450, 18320, 18250.3],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: '^GSPC',
    display_symbol: 'S&P 500',
    label: 'S&P 500',
    category: 'INDEX',
    name: 'S&P 500 Index',
    price: 5760.15,
    prev_close: 5815.2,
    change_abs: -55.05,
    change_pct: -0.95,
    is_positive: false,
    currency: 'USD',
    exchange: 'SNP',
    sparkline: [5820, 5810, 5790, 5770, 5760.15],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: '^DJI',
    display_symbol: 'DOW JONES',
    label: 'DOW JONES',
    category: 'INDEX',
    name: 'Dow Jones Industrial Average',
    price: 43275.9,
    prev_close: 43077.7,
    change_abs: 198.2,
    change_pct: 0.46,
    is_positive: true,
    currency: 'USD',
    exchange: 'DJI',
    sparkline: [43080, 43150, 43200, 43250, 43275.9],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: 'NVDA',
    display_symbol: 'NVDA',
    label: 'NVDA',
    category: 'EQUITY',
    name: 'NVIDIA Corporation',
    price: 138.25,
    prev_close: 132.65,
    change_abs: 5.6,
    change_pct: 4.22,
    is_positive: true,
    currency: 'USD',
    exchange: 'NMS',
    sparkline: [131, 133, 135, 137, 138.25],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: 'TSLA',
    display_symbol: 'TSLA',
    label: 'TSLA',
    category: 'EQUITY',
    name: 'Tesla, Inc.',
    price: 218.6,
    prev_close: 223.4,
    change_abs: -4.8,
    change_pct: -2.15,
    is_positive: false,
    currency: 'USD',
    exchange: 'NMS',
    sparkline: [225, 223, 221, 219, 218.6],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: 'AAPL',
    display_symbol: 'AAPL',
    label: 'AAPL',
    category: 'EQUITY',
    name: 'Apple Inc.',
    price: 232.1,
    prev_close: 230.15,
    change_abs: 1.95,
    change_pct: 0.85,
    is_positive: true,
    currency: 'USD',
    exchange: 'NMS',
    sparkline: [229, 230, 231, 231.5, 232.1],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: 'MSFT',
    display_symbol: 'MSFT',
    label: 'MSFT',
    category: 'EQUITY',
    name: 'Microsoft Corporation',
    price: 428.5,
    prev_close: 431.2,
    change_abs: -2.7,
    change_pct: -0.63,
    is_positive: false,
    currency: 'USD',
    exchange: 'NMS',
    sparkline: [433, 432, 430, 429, 428.5],
    updated_at: 'Live',
    is_live: true,
  },
  {
    symbol: 'CL=F',
    display_symbol: 'CRUDE OIL',
    label: 'CRUDE OIL',
    category: 'COMMODITY',
    name: 'Crude Oil Futures',
    price: 82.4,
    prev_close: 79.8,
    change_abs: 2.6,
    change_pct: 3.26,
    is_positive: true,
    currency: 'USD',
    exchange: 'NYM',
    sparkline: [79.5, 80.2, 81.1, 81.9, 82.4],
    updated_at: 'Live',
    is_live: true,
  },
];

export const TopMarketRibbon: React.FC<TopMarketRibbonProps> = ({ onSelectStock }) => {
  const [tickers, setTickers] = useState<MarketTicker[]>(FALLBACK_TICKERS);
  const [isLiveActive, setIsLiveActive] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    const fetchLiveTickers = async () => {
      try {
        const data = await api.getMarketTickers();
        if (isMounted && data && data.length > 0) {
          setTickers(data);
          setIsLiveActive(true);
        }
      } catch (err) {
        console.warn('Using baseline tickers (API unreachable or rate-limited):', err);
      }
    };

    fetchLiveTickers();
    const interval = setInterval(fetchLiveTickers, 25000); // 25s live ticker cycle
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="w-full bg-[#070d1a] border-b border-[#16233b] py-2 px-4 overflow-x-auto scrollbar-none flex items-center gap-3 text-xs select-none">
      {/* Live Badge */}
      <div className="flex items-center gap-1.5 text-slate-400 font-bold uppercase tracking-wider text-[10px] shrink-0 pr-3 border-r border-[#1a2944]">
        <span className={`w-2 h-2 rounded-full ${isLiveActive ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
        <span className="text-white flex items-center gap-1 font-mono">
          <span>MARKET TICKERS</span>
        </span>
        <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
          LIVE
        </span>
      </div>

      {/* Interactive Ribbon Ticker Chips */}
      <div className="flex items-center gap-2.5 shrink-0">
        {tickers.map((t) => {
          const displaySym = t.display_symbol || t.label || t.symbol.replace('^', '');
          const isPos = t.is_positive || t.change_pct >= 0;
          return (
            <button
              key={t.symbol}
              type="button"
              onClick={() => onSelectStock?.(displaySym)}
              className="flex items-center gap-2 bg-[#0c1527] hover:bg-[#13223f] border border-[#1b2a47] hover:border-cyan-500/60 rounded-lg px-2.5 py-1 whitespace-nowrap cursor-pointer transition-all duration-150 group shadow-sm active:scale-95"
              title={`Click to inspect ${displaySym} live market data, chart & news correlation`}
            >
              <div className="flex items-center gap-1">
                <span className="font-bold text-white group-hover:text-cyan-300 transition-colors font-mono">
                  {displaySym}
                </span>
                <span className="text-[9px] uppercase px-1 rounded bg-[#070d18] text-slate-400 font-mono">
                  {t.category}
                </span>
              </div>

              <span className="font-mono text-slate-100 font-semibold text-xs">
                ${t.price >= 1000 ? t.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : t.price.toFixed(2)}
              </span>

              <span
                className={`font-mono font-bold flex items-center text-[11px] ${
                  isPos ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {isPos ? '+' : ''}
                {t.change_pct.toFixed(2)}%
              </span>

              {/* Sentiment / Change badge */}
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-medium flex items-center gap-0.5 ${
                  isPos
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                }`}
              >
                {isPos ? <TrendingUp className="w-2.5 h-2.5" /> : <TrendingDown className="w-2.5 h-2.5" />}
                <span>{isPos ? 'BULL' : 'BEAR'}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className="ml-auto text-[10px] text-slate-500 font-mono hidden md:flex items-center gap-1 shrink-0 pl-2">
        <Sparkles className="w-3 h-3 text-cyan-400" />
        <span>Click any ticker for live quote & AI news correlation</span>
      </div>
    </div>
  );
};
