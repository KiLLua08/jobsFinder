"use client";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Briefcase, LayoutDashboard, Search, BrainCircuit, Tags, Play } from "lucide-react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const nav = [
  { href: "/", label: "Home", icon: Briefcase },
  { href: "/jobs", label: "Jobs", icon: Search },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/classify", label: "Classify", icon: BrainCircuit },
  { href: "/scrape", label: "Scrape", icon: Play },
  { href: "/label", label: "Label", icon: Tags },
];

function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-60 bg-white border-r border-slate-200 sticky top-0 h-screen flex flex-col">
      <div className="px-4 py-5 border-b border-slate-200">
        <Link href="/" className="flex items-center gap-2 text-lg font-bold text-slate-900">
          <Briefcase className="h-5 w-5 text-indigo-600" />
          JobsFinder
        </Link>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map((item) => {
          const Icon = item.icon;
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <Icon className={`h-4 w-4 ${active ? "text-indigo-600" : ""}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-slate-200 text-xs text-slate-400">
        AI-powered job finder
      </div>
    </aside>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 p-6 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
