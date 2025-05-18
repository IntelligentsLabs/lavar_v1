// src/components/ui/card.d.ts
declare module "@/components/ui/card" {
  import React from "react";

  export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    /** Content inside the card */
    children: React.ReactNode;
    /** Extra CSS classes */
    className?: string;
  }
  export function Card(props: CardProps): JSX.Element;

  export interface CardContentProps
    extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
  }
  export function CardContent(props: CardContentProps): JSX.Element;

  export interface CardFooterProps
    extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
  }
  export function CardFooter(props: CardFooterProps): JSX.Element;
}
