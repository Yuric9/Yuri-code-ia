import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Yuri Code AI",
  description: "Assistente de programação com IA",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
