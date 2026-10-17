import React from 'react';
import {
  Newspaper,
  LayoutDashboard,
  BrainCircuit,
  ShieldAlert,
  BarChart3,
  Settings,
  Scale,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export type NavTab = 'news' | 'overview' | 'analysis' | 'review' | 'performance' | 'settings';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  pendingReviewCount: number;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  pendingReviewCount,
  collapsed,
  onToggleCollapse,
}) => {
  const navItems = [
    { id: 'news' as NavTab, label: 'News Stream', icon: Newspaper, badge: null },
    { id: 'overview' as NavTab, label: 'Overview', icon: LayoutDashboard, badge: null },
    { id: 'analysis' as NavTab, label: 'Gemini Intel', icon: BrainCircuit, badge: null },
    {
      id: 'review' as NavTab,
      label: 'Review Queue',
      icon: ShieldAlert,
      badge: pendingReviewCount > 0 ? pendingReviewCount : null,
      badgeColor: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    },
    { id: 'performance' as NavTab, label: 'Benchmarks', icon: BarChart3, badge: null },
    { id: 'settings' as NavTab, label: 'Configuration', icon: Settings, badge: null },
  ];

  return (
    <aside
      className={`bg-[#070c18] border-r border-[#16233b] flex flex-col justify-between transition-all duration-300 select-none ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Top Menu Section */}
      <div className="p-3">
        {/* Toggle Collapse Button */}
        <div className="flex justify-end mb-2">
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#111c34] transition-colors"
            title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-3 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-teal/20 to-brand-cyan/10 text-white border border-brand-teal/40 shadow-sm shadow-brand-teal/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#0c1527] border border-transparent'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-5 h-5 shrink-0 ${
                    isActive ? 'text-brand-teal' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                {!collapsed && (
                  <span className="truncate text-left flex-1 font-medium">{item.label}</span>
                )}
                {!collapsed && item.badge !== null && (
                  <span
                    className={`text-[11px] font-mono px-2 py-0.5 rounded-full font-bold ${item.badgeColor}`}
                  >
                    {item.badge}
                  </span>
                )}
                {collapsed && item.badge !== null && (
                  <span className="w-2 h-2 rounded-full bg-amber-400 absolute top-2 right-2 animate-ping" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Regulatory Notice & Compliance Box */}
      {!collapsed && (
        <div className="p-4 m-3 rounded-xl bg-[#091122] border border-[#16233b] text-[11px] text-slate-400 leading-relaxed">
          <div className="flex items-center gap-1.5 text-slate-300 font-semibold mb-1">
            <Scale className="w-3.5 h-3.5 text-brand-teal" />
            <span>Research Disclaimer</span>
          </div>
          <p className="text-slate-500 text-[10px]">
            Educational purposes only. SignalFlow AI does not execute trades or provide financial advice.
          </p>
        </div>
      )}
    </aside>
  );
};
