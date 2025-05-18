import React, { ReactNode, HTMLAttributes } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Content inside the card */
  children: ReactNode;
  /** Additional class names */
  className?: string;
}

export function Card({ children, className = "", ...rest }: CardProps) {
  return (
    <div className={`card ${className}`} {...rest}>
      {children}
    </div>
  );
}

interface CardContentProps extends HTMLAttributes<HTMLDivElement> {
  /** Content inside the card body */
  children: ReactNode;
  /** Additional class names */
  className?: string;
}

export function CardContent({ children, className = "", ...rest }: CardContentProps) {
  return (
    <div className={`card-content ${className}`} {...rest}>
      {children}
    </div>
  );
}
