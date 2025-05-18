
declare module '@/components/ui/card' {
  import React from 'react';

  export function Card(props: { children: React.ReactNode }): JSX.Element;
  export function CardContent(props: { children: React.ReactNode }): JSX.Element;
  export function CardFooter(props: { children: React.ReactNode }): JSX.Element;
}
