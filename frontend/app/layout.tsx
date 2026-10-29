
export default function RootLayout({children}:{children:React.ReactNode}) {
 return (<html><head><script src="https://cdn.tailwindcss.com"></script></head><body className="bg-zinc-950 text-zinc-100">{children}</body></html>)
}
