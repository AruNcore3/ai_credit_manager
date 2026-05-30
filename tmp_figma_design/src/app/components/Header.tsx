import { Menu, X } from "lucide-react";
import { useState } from "react";

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-lg">
      <nav className="mx-auto flex max-w-7xl items-center justify-between p-6 lg:px-8">
        <div className="flex lg:flex-1">
          <a href="#" className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary to-muted-foreground" />
            <span className="font-semibold">API Platform</span>
          </a>
        </div>

        <div className="flex lg:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="inline-flex items-center justify-center rounded-md p-2.5 text-foreground"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        <div className="hidden lg:flex lg:gap-x-12">
          <a href="#features" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
            Features
          </a>
          <a href="#documentation" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
            Documentation
          </a>
          <a href="#pricing" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
            Pricing
          </a>
          <a href="#api" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
            API Reference
          </a>
        </div>

        <div className="hidden lg:flex lg:flex-1 lg:justify-end lg:gap-x-4">
          <a href="#" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
            Sign in
          </a>
          <a
            href="#"
            className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Get started
          </a>
        </div>
      </nav>

      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-border/40">
          <div className="space-y-2 px-6 pb-6 pt-6">
            <a
              href="#features"
              className="block rounded-lg px-3 py-2 text-base hover:bg-muted"
              onClick={() => setMobileMenuOpen(false)}
            >
              Features
            </a>
            <a
              href="#documentation"
              className="block rounded-lg px-3 py-2 text-base hover:bg-muted"
              onClick={() => setMobileMenuOpen(false)}
            >
              Documentation
            </a>
            <a
              href="#pricing"
              className="block rounded-lg px-3 py-2 text-base hover:bg-muted"
              onClick={() => setMobileMenuOpen(false)}
            >
              Pricing
            </a>
            <a
              href="#api"
              className="block rounded-lg px-3 py-2 text-base hover:bg-muted"
              onClick={() => setMobileMenuOpen(false)}
            >
              API Reference
            </a>
            <div className="border-t border-border/40 pt-4 mt-4">
              <a href="#" className="block rounded-lg px-3 py-2 text-base hover:bg-muted">
                Sign in
              </a>
              <a
                href="#"
                className="mt-2 block rounded-full bg-primary px-4 py-2 text-center text-sm text-primary-foreground"
              >
                Get started
              </a>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
