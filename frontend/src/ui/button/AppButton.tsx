import Button from "@mui/material/Button";
import type { ButtonProps } from "@mui/material/Button";

export default function AppButton({
    children,
    variant = "contained",
    color = "primary",
    sx,
    ...props
}: ButtonProps) {
    return (
        <Button
            variant={variant}
            color={color}
            disableElevation
            sx={{
                textTransform: "none",
                fontWeight: 600,
                borderRadius: 2,
                px: 2,
                py: 1,
                ...sx,
            }}
            {...props}
        >
            {children}
        </Button>
    );
}