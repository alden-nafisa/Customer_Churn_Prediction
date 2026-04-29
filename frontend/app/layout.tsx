import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Customer Churn Control Room",
  description: "Next.js frontend for the FastAPI churn prediction backend.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
