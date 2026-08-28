import { Clock3 } from "lucide-react";

export default function TimeRangeSelector() {
    return <button className="topbar-control" type="button" disabled title="Time filtering is not configured"><Clock3 size={11} />Last 7 Days</button>;
}
