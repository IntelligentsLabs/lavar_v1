// src/components/ui/button.d.ts
declare module "@/components/ui/button" {
  import type { ReactNode, ButtonHTMLAttributes } from "react";

  export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    children: ReactNode;
    variant?: string;
    size?: string;
    className?: string;
  }

  export function Button(props: ButtonProps): JSX.Element;
}
