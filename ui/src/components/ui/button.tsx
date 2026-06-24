// Button — shadcn-style primitive restyled to the Warm-Frontier tokens.
// Variants map to roles: accent (primary CTA), ghost (toolbar), subtle (quiet surface), danger.
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded font-medium transition-colors duration-150 ease-out-quart disabled:pointer-events-none disabled:opacity-45 select-none",
  {
    variants: {
      variant: {
        accent: "bg-accent text-[#F4EFE6] hover:bg-accent-hover shadow-glow-accent",
        ghost: "text-ink-muted hover:bg-surface-alt hover:text-ink",
        subtle: "bg-surface border border-border text-ink hover:border-border-subtle hover:bg-surface-alt",
        danger: "bg-danger text-[#F4EFE6] hover:brightness-95",
        link: "text-accent underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-meta",
        md: "h-10 px-4 text-ui",
        lg: "h-11 px-5 text-ui",
        icon: "h-9 w-9",
        "icon-sm": "h-8 w-8",
      },
    },
    defaultVariants: { variant: "subtle", size: "md" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
    );
  }
);
Button.displayName = "Button";

export { buttonVariants };
