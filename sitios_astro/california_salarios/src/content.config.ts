import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const integrations = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/integrations" }),
  schema: ({ image }) =>
    z.object({
      integration: z.string(),
      description: z.string(),
      email: z.string(),
      permissions: z.array(z.string()),
      details: z.array(
        z.object({
          title: z.string(),
          value: z.string(),
          url: z.string().optional(),
        })
      ),
      logo: z.object({
        url: image(),
        alt: z.string(),
      }),
    }),
});

const helpcenter = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/helpcenter" }),
  schema: z.object({
    page: z.string(),
    description: z.string(),
    category: z.string().optional(),
    keywords: z.array(z.string()).optional(),
    lastUpdated: z.string().optional(),
    faq: z
      .array(z.object({ question: z.string(), answer: z.string() }))
      .optional(),
  }),
});

const changelog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/changelog" }),
  schema: ({ image }) =>
    z.object({
      page: z.string(),
      description: z.string(),
      pubDate: z.coerce.date(),
      image: z.object({
        url: image(),
        alt: z.string(),
      }),
    }),
});

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.coerce.date(),
  }),
});

const posts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.coerce.date(),
      description: z.string(),
      author: z.string(),
      image: z.object({
        url: image(),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

export const collections = {
  helpcenter,
  changelog,
  legal,
  posts,
  integrations,
};
