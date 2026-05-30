import { ArrowRight, Sparkles } from "lucide-react";
import { motion } from "motion/react";

export function Hero() {
  return (
    <div className="relative isolate overflow-hidden pt-24 pb-16 sm:pt-32 sm:pb-24">
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-muted/50 to-background" />

      <div className="absolute inset-y-0 right-1/2 -z-10 mr-16 w-[200%] origin-bottom-left skew-x-[-30deg] bg-background shadow-xl shadow-primary/10 ring-1 ring-border/10 sm:mr-28 lg:mr-0 xl:mr-16 xl:origin-center" />

      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:mx-0 lg:grid lg:max-w-none lg:grid-cols-2 lg:gap-x-16 lg:gap-y-6 xl:grid-cols-1 xl:grid-rows-1 xl:gap-x-8">
          <div className="max-w-xl lg:max-w-none">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 rounded-full bg-muted px-4 py-1.5 text-sm mb-8"
            >
              <Sparkles className="h-4 w-4" />
              <span>New: Advanced AI Models Released</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-6xl lg:text-7xl tracking-tight mb-6"
            >
              Build the future with our{" "}
              <span className="bg-gradient-to-r from-primary to-muted-foreground bg-clip-text text-transparent">
                powerful API
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg leading-8 text-muted-foreground mb-10 max-w-xl"
            >
              Integrate cutting-edge AI capabilities into your applications with our easy-to-use API.
              Start building in minutes with comprehensive documentation and support.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex items-center gap-x-6"
            >
              <a
                href="#"
                className="group inline-flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm text-primary-foreground shadow-lg hover:bg-primary/90 transition-all"
              >
                Get started for free
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </a>
              <a href="#documentation" className="text-sm leading-6 text-foreground hover:text-muted-foreground transition-colors">
                View documentation <span aria-hidden="true">→</span>
              </a>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="mt-10 lg:mt-0 lg:col-span-2 xl:col-span-1 xl:row-span-2"
          >
            <div className="relative overflow-hidden rounded-2xl bg-card border border-border shadow-2xl">
              <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                <div className="h-3 w-3 rounded-full bg-destructive" />
                <div className="h-3 w-3 rounded-full bg-chart-4" />
                <div className="h-3 w-3 rounded-full bg-chart-2" />
              </div>
              <div className="p-6 font-mono text-sm">
                <div className="text-muted-foreground"># Install the package</div>
                <div className="text-chart-2 mt-2">npm install api-platform-sdk</div>
                <div className="text-muted-foreground mt-6"># Make your first request</div>
                <div className="mt-2">
                  <span className="text-chart-1">import</span>{" "}
                  <span className="text-foreground">{'{ APIClient }'}</span>{" "}
                  <span className="text-chart-1">from</span>{" "}
                  <span className="text-chart-4">'api-platform-sdk'</span>
                </div>
                <div className="mt-4">
                  <span className="text-chart-1">const</span>{" "}
                  <span className="text-foreground">client</span>{" "}
                  <span className="text-chart-1">=</span>{" "}
                  <span className="text-chart-1">new</span>{" "}
                  <span className="text-foreground">APIClient</span>
                  <span className="text-foreground">({'{'}</span>
                </div>
                <div className="ml-4">
                  <span className="text-foreground">apiKey:</span>{" "}
                  <span className="text-chart-4">'your-api-key'</span>
                </div>
                <div>
                  <span className="text-foreground">{'})'}</span>
                </div>
                <div className="mt-4">
                  <span className="text-chart-1">const</span>{" "}
                  <span className="text-foreground">response</span>{" "}
                  <span className="text-chart-1">=</span>{" "}
                  <span className="text-chart-1">await</span>{" "}
                  <span className="text-foreground">client</span>
                  <span className="text-foreground">.generate({'{'}</span>
                </div>
                <div className="ml-4">
                  <span className="text-foreground">prompt:</span>{" "}
                  <span className="text-chart-4">'Hello, world!'</span>
                </div>
                <div>
                  <span className="text-foreground">{'})'}</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
