import { Book, Terminal, Wrench, MessageSquare } from "lucide-react";
import { motion } from "motion/react";

const resources = [
  {
    name: "Getting Started",
    description: "Learn the basics and make your first API call in under 5 minutes.",
    icon: Book,
    href: "#",
  },
  {
    name: "API Reference",
    description: "Complete documentation of all endpoints, parameters, and responses.",
    icon: Terminal,
    href: "#",
  },
  {
    name: "Guides & Tutorials",
    description: "Step-by-step guides for common use cases and integration patterns.",
    icon: Wrench,
    href: "#",
  },
  {
    name: "Community",
    description: "Join thousands of developers building with our API.",
    icon: MessageSquare,
    href: "#",
  },
];

export function Documentation() {
  return (
    <div id="documentation" className="py-24 sm:py-32 bg-muted/30">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl sm:text-4xl tracking-tight">
            Resources to help you succeed
          </h2>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            Comprehensive documentation, guides, and community support to get you building quickly.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            {resources.map((resource, index) => (
              <motion.a
                key={resource.name}
                href={resource.href}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group relative flex items-start gap-6 rounded-2xl border border-border bg-card p-8 hover:border-primary/50 transition-all hover:shadow-lg"
              >
                <div className="flex h-12 w-12 flex-none items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <resource.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold group-hover:text-primary transition-colors">
                    {resource.name}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {resource.description}
                  </p>
                  <p className="mt-4 text-sm text-primary group-hover:underline">
                    Learn more →
                  </p>
                </div>
              </motion.a>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-16 rounded-3xl bg-gradient-to-br from-primary/10 to-muted p-8 lg:p-16"
        >
          <div className="mx-auto max-w-3xl text-center">
            <h3 className="text-2xl sm:text-3xl tracking-tight">
              Ready to get started?
            </h3>
            <p className="mt-4 text-lg text-muted-foreground">
              Join thousands of developers building with our API. Get your API key and start building in minutes.
            </p>
            <div className="mt-8 flex items-center justify-center gap-x-6">
              <a
                href="#"
                className="rounded-full bg-primary px-6 py-3 text-sm text-primary-foreground shadow-lg hover:bg-primary/90 transition-colors"
              >
                Create free account
              </a>
              <a href="#" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
                Contact sales <span aria-hidden="true">→</span>
              </a>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
