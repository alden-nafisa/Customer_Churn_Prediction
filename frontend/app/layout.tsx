import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "../components/Sidebar";

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
      <body>
        <div className="app-frame">
          <Sidebar />
          <div className="app-main">{children}</div>
        </div>
      </body>
    </html>
  );
}
