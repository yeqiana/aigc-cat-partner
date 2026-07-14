import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIGC Cat Partner",
  description: "AIGC Cat Partner prompt generation entry page.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
