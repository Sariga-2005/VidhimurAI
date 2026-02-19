interface RoadmapData {
    immediate_actions: string[];
    evidence_checklist: string[];
    legal_notice_strategy: string[];
    pre_litigation_options: string[];
    litigation_strategy: string[];
    estimated_timeline: string;
    cost_considerations: string[];
    risk_assessment: string[] | string;
    escalation_path: string[];
}

interface LegalTimelineProps {
    roadmap: RoadmapData;
    issueType?: string;
    legalStrength?: string;
}

const stages = [
    { key: 'immediate_actions' as const, label: 'Immediate Actions', icon: '1', desc: 'First 7 days' },
    { key: 'evidence_checklist' as const, label: 'Evidence Collection', icon: '2', desc: 'Gather proof' },
    { key: 'legal_notice_strategy' as const, label: 'Legal Notice', icon: '3', desc: 'Formal notice' },
    { key: 'pre_litigation_options' as const, label: 'Pre-Litigation', icon: '4', desc: 'Negotiation & mediation' },
    { key: 'litigation_strategy' as const, label: 'Litigation', icon: '5', desc: 'Court proceedings' },
    { key: 'escalation_path' as const, label: 'Escalation', icon: '6', desc: 'Appeals & review' },
];

const strengthColors: Record<string, string> = {
    Strong: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    Moderate: 'text-amber-700 bg-amber-50 border-amber-200',
    Weak: 'text-red-600 bg-red-50 border-red-200',
};

const LegalTimeline = ({ roadmap, issueType, legalStrength }: LegalTimelineProps) => {
    return (
        <div className="rounded-xl border border-official-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-bold text-official-900 uppercase tracking-wider">
                    Legal Strategy Timeline
                </h3>
                {legalStrength && (
                    <span className={`px-2 py-0.5 rounded-md border text-xs font-bold ${strengthColors[legalStrength] || 'text-official-600 bg-official-50 border-official-200'}`}>
                        {legalStrength}
                    </span>
                )}
            </div>
            {issueType && (
                <p className="text-xs text-official-500 mb-1">{issueType}</p>
            )}
            {roadmap.estimated_timeline && (
                <p className="text-xs text-official-400 mb-6">
                    Estimated Duration: <span className="font-semibold text-official-600">{roadmap.estimated_timeline}</span>
                </p>
            )}


            {/* Horizontal timeline for larger screens */}
            <div className="hidden md:block">
                {/* Connector line */}
                <div className="relative mb-8">
                    <div className="absolute top-4 left-0 right-0 h-0.5 bg-official-200"></div>
                    <div className="flex justify-between relative">
                        {stages.map((stage) => {
                            const items = roadmap[stage.key];
                            const hasItems = Array.isArray(items) && items.length > 0;
                            return (
                                <div key={stage.key} className="flex flex-col items-center" style={{ width: `${100 / stages.length}%` }}>
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-all duration-300 ${hasItems
                                        ? 'bg-[#1B3A5C] text-white shadow-md'
                                        : 'bg-official-100 text-official-400 border border-official-200'
                                        }`}>
                                        {stage.icon}
                                    </div>
                                    <p className={`mt-2 text-xs font-semibold text-center leading-tight ${hasItems ? 'text-official-800' : 'text-official-400'}`}>
                                        {stage.label}
                                    </p>
                                    <p className="text-[10px] text-official-400 mt-0.5">{stage.desc}</p>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Stage detail cards in horizontal grid */}
                <div className="grid grid-cols-3 gap-4">
                    {stages.map((stage) => {
                        const items = roadmap[stage.key];
                        if (!Array.isArray(items) || items.length === 0) return null;
                        return (
                            <div key={stage.key} className="rounded-lg border border-official-100 bg-official-50/50 p-4">
                                <h4 className="text-xs font-bold text-[#1B3A5C] uppercase tracking-wide mb-2">{stage.label}</h4>
                                <ul className="space-y-1.5">
                                    {items.map((item, j) => (
                                        <li key={j} className="flex gap-2 text-xs text-official-600 leading-relaxed">
                                            <span className="text-[#1B3A5C] mt-0.5 shrink-0">&#8226;</span>
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Vertical timeline for mobile */}
            <div className="md:hidden space-y-0">
                {stages.map((stage, i) => {
                    const items = roadmap[stage.key];
                    if (!Array.isArray(items) || items.length === 0) return null;
                    return (
                        <div key={stage.key} className="flex gap-4 group">
                            <div className="flex flex-col items-center">
                                <div className="w-8 h-8 rounded-full bg-[#1B3A5C] text-white flex items-center justify-center text-sm font-bold shrink-0 shadow-sm">
                                    {stage.icon}
                                </div>
                                {i < stages.length - 1 && (
                                    <div className="w-0.5 flex-1 bg-official-200 mt-1"></div>
                                )}
                            </div>
                            <div className="pb-6 flex-1">
                                <h4 className="text-xs font-bold text-[#1B3A5C] uppercase tracking-wide mb-1">{stage.label}</h4>
                                <p className="text-[10px] text-official-400 mb-2">{stage.desc}</p>
                                <ul className="space-y-1">
                                    {items.map((item, j) => (
                                        <li key={j} className="flex gap-2 text-xs text-official-600 leading-relaxed">
                                            <span className="text-[#1B3A5C] mt-0.5 shrink-0">&#8226;</span>
                                            <span>{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Bottom metadata: cost & risk */}
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {roadmap.cost_considerations && roadmap.cost_considerations.length > 0 && (
                    <div className="rounded-lg border border-official-100 bg-official-50/50 p-4">
                        <h4 className="text-xs font-bold text-official-700 uppercase tracking-wide mb-2">Cost Considerations</h4>
                        <ul className="space-y-1">
                            {roadmap.cost_considerations.map((c, i) => (
                                <li key={i} className="text-xs text-official-600 flex gap-2">
                                    <span className="text-official-400 shrink-0">&#8226;</span>
                                    <span>{c}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                {roadmap.risk_assessment && (
                    <div className="rounded-lg border border-official-100 bg-official-50/50 p-4">
                        <h4 className="text-xs font-bold text-official-700 uppercase tracking-wide mb-2">Risk Assessment</h4>
                        {Array.isArray(roadmap.risk_assessment) ? (
                            <ul className="space-y-1">
                                {roadmap.risk_assessment.map((r, i) => (
                                    <li key={i} className="text-xs text-official-600 flex gap-2">
                                        <span className="text-official-400 shrink-0">&#8226;</span>
                                        <span>{r}</span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-xs text-official-600">{roadmap.risk_assessment}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default LegalTimeline;
