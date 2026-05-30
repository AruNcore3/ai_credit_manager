import { Zap, Shield, Code2, Globe, Clock, TrendingUp } from "lucide-react";
import { motion } from "motion/react";

const features = [
  {
    name: "Lightning Fast",
    description: "Get responses in milliseconds with our optimized infrastructure and global edge network.",
    icon: Zap,
  },
  {
    name: "Enterprise Security",
    description: "Bank-level encryption, SOC 2 compliant, and GDPR ready to protect your data.",
    icon: Shield,
  },
  {
    name: "Easy Integration",
    description: "Simple REST API with SDKs for Python, Node.js, Go, and more. Start coding in minutes.",
    icon: Code2,
  },
  {
    name: "Global Coverage",
    description: "Deployed across 50+ regions worldwide for low latency and high availability.",
    icon: Globe,
  },
  {
    name: "99.9% Uptime",
    description: "Reliable infrastructure with automatic failover and real-time monitoring.",
    icon: Clock,
  },
  {
    name: "Scale Seamlessly",
    description: "From prototype to production, our API scales with your needs automatically.",
    icon: TrendingUp,
  },
];

export function Features() {
  return (
    <div id="features" className="py-24 sm:py-32 bg-muted/30">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl sm:text-4xl tracking-tight">
            Everything you need to build amazing products
          </h2>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            Our API provides powerful features designed for developers who want to ship fast without compromising on quality.
          </p>
        </div>

        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div
                key={feature.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="flex flex-col"
              >
                <dt className="flex items-center gap-x-3">
                  <div className="rounded-lg bg-primary/10 p-2 ring-1 ring-primary/20">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <span className="font-semibold">{feature.name}</span>
                </dt>
                <dd className="mt-4 flex flex-auto flex-col leading-7 text-muted-foreground">
                  <p className="flex-auto">{feature.description}</p>
                </dd>
              </motion.div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
