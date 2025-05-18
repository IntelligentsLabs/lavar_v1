
declare module '@/components/ui/button' {
  import React from 'react';

  export function Button(props: { children: React.ReactNode, onClick: () => void }): JSX.Element;
}
