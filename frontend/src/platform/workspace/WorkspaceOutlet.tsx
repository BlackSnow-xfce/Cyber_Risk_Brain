import DashboardLayout from "@/components/dashboard/DashboardLayout";
import DashboardGrid from "@/components/dashboard/DashboardGrid";
import KpiCard from "@/components/card/kpi/KpiCard";

export default function WorkspaceOutlet() {
    return (
        <>
            <DashboardGrid>
                <KpiCard
                    title="Critical Findings"
                    value="128"
                    change="+12%"
                    trend="up"
                />

                <KpiCard
                    title="Internet Facing"
                    value="43"
                    change="-3%"
                    trend="down"
                />

                <KpiCard
                    title="Attack Paths"
                    value="17"
                    change="+2"
                    trend="up"
                />

                <KpiCard
                    title="Decision Confidence"
                    value="98%"
                    trend="neutral"
                />
            </DashboardGrid>

            <DashboardLayout />
        </>
    );
}