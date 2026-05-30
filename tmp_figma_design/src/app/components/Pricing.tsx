import { Check } from "lucide-react";
import { motion } from "motion/react";

const tiers = [
  {
    name: "Free",
    id: "tier-free",
    price: "$0",
    description: "Perfect for experimenting and small projects.",
    features: [
      "100,000 tokens per month",
      "Community support",
      "Basic rate limits",
      "Standard models",
    ],
    featured: false,
  },
  {
    name: "Pro",
    id: "tier-pro",
    price: "$49",
    description: "For production applications and growing teams.",
    features: [
      "5M tokens per month",
      "Priority support",
      "Higher rate limits",
      "Advanced models",
      "Usage analytics",
      "Team collaboration",
    ],
    featured: true,
  },
  {
    name: "Enterprise",
    id: "tier-enterprise",
    price: "Custom",
    description: "For large-scale applications with custom needs.",
    features: [
      "Unlimited tokens",
      "Dedicated support",
      "Custom rate limits",
      "All models including beta",
      "Advanced analytics",
      "SLA guarantee",
      "Custom integrations",
      "Volume discounts",
    ],
    featured: false,
  },
];

export function Pricing() {
  return (
    <div id="pricing" className="py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-3xl sm:text-4xl tracking-tight">
            Pricing that scales with you
          </h2>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            Choose the perfect plan for your needs. All plans include our core features with no hidden fees.
          </p>
        </div>

        <div className="isolate mx-auto mt-16 grid max-w-md grid-cols-1 gap-y-8 sm:mt-20 lg:mx-0 lg:max-w-none lg:grid-cols-3 lg:gap-x-8 xl:gap-x-8">
          {tiers.map((tier, index) => (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`rounded-3xl p-8 ring-1 ${
                tier.featured
                  ? "bg-primary/5 ring-primary shadow-lg scale-105"
                  : "bg-card ring-border"
              }`}
            >
              <h3 id={tier.id} className="text-lg leading-8">
                {tier.name}
              </h3>
              <p className="mt-4 text-sm leading-6 text-muted-foreground">
                {tier.description}
              </p>
              <p className="mt-6 flex items-baseline gap-x-1">
                <span className="text-4xl tracking-tight">{tier.price}</span>
                {tier.price !== "Custom" && (
                  <span className="text-sm leading-6 text-muted-foreground">/month</span>
                )}
              </p>
              <a
                href="#"
                className={`mt-6 block rounded-full py-2.5 px-3.5 text-center text-sm transition-colors ${
                  tier.featured
                    ? "bg-primary text-primary-foreground shadow-sm hover:bg-primary/90"
                    : "bg-muted text-foreground hover:bg-muted/80"
                }`}
              >
                {tier.price === "Custom" ? "Contact sales" : "Get started"}
              </a>
              <ul className="mt-8 space-y-3">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex gap-x-3">
                    <Check className="h-6 w-5 flex-none text-primary" />
                    <span className="text-sm leading-6 text-muted-foreground">{feature}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
