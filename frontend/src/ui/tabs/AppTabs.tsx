import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";

interface AppTabsProps {
    value: number;
    onChange: (value: number) => void;
    labels: string[];
}

export default function AppTabs({
    value,
    onChange,
    labels,
}: AppTabsProps) {
    return (
        <Tabs
            value={value}
            onChange={(_, newValue) => onChange(newValue)}
            variant="scrollable"
            scrollButtons="auto"
        >
            {labels.map((label) => (
                <Tab
                    key={label}
                    label={label}
                    disableRipple
                />
            ))}
        </Tabs>
    );
}