import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const baseSchema = z.object({
  body: z.string().optional(),
});

const posts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: baseSchema.extend({
    title: z.string().optional(),
    pubDate: z.union([z.string(), z.date()]).optional(),
    description: z.string().optional(),
    author: z.string().optional(),
    image: z
      .object({
        url: z.string().optional(),
        alt: z.string().optional(),
      })
      .optional(),
    tags: z.array(z.string()).optional(),
  }),
});

const integrations = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/integrations" }),
  schema: baseSchema.extend({
    integration: z.string().optional(),
    description: z.string().optional(),
    email: z.string().optional(),
    permissions: z.array(z.string()).optional(),
    details: z.array(z.record(z.string(), z.unknown())).optional(),
    logo: z.record(z.string(), z.unknown()).optional(),
  }),
});

const jobs = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/jobs" }),
  schema: baseSchema.extend({
    page: z.string().optional(),
    details: z.record(z.string(), z.unknown()).optional(),
  }),
});

const team = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/team" }),
  schema: baseSchema.extend({
    name: z.string().optional(),
    role: z.string().optional(),
    intro: z.string().optional(),
    education: z.array(z.string()).optional(),
    experience: z.array(z.string()).optional(),
    avatar: z.record(z.string(), z.unknown()).optional(),
  }),
});

const customers = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/customers" }),
  schema: baseSchema.extend({
    customer: z.string().optional(),
    challengesAndSolutions: z.array(z.record(z.string(), z.unknown())).optional(),
    results: z.array(z.string()).optional(),
    about: z.string().optional(),
    details: z
      .union([
        z.array(z.record(z.string(), z.unknown())),
        z.record(z.string(), z.unknown()),
      ])
      .optional(),
    logo: z.record(z.string(), z.unknown()).optional(),
  }),
});

const changelog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/changelog" }),
  schema: baseSchema.extend({
    page: z.string().optional(),
    description: z.string().optional(),
    pubDate: z.union([z.string(), z.date()]).optional(),
    image: z.record(z.string(), z.unknown()).optional(),
  }),
});

const helpcenter = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/helpcenter" }),
  schema: baseSchema.extend({
    page: z.string().optional(),
    description: z.string().optional(),
  }),
});

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: baseSchema.extend({
    page: z.string().optional(),
    pubDate: z.union([z.string(), z.date()]).optional(),
  }),
});

const whitepaper = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/whitepaper" }),
  schema: baseSchema.extend({
    page: z.string().optional(),
    pubDate: z.union([z.string(), z.date()]).optional(),
  }),
});

export const collections = {
  posts,
  integrations,
  jobs,
  team,
  customers,
  changelog,
  helpcenter,
  legal,
  whitepaper,
};
