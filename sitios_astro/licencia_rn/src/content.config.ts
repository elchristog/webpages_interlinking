import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const helpcenter = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/helpcenter" }),
  schema: z.object({
    title: z.string(),
    intro: z.string(),
  }),
});

const changelog = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/changelog" }),
  schema: ({ image }) =>
    z.object({
      page: z.string(),
      description: z.string(),
      pubDate: z.date(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
    }),
});

const infopages = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/infopages" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.date(),
  }),
});

const integrations = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/integrations" }),
  schema: ({ image }) =>
    z.object({
      email: z.string(),
      integration: z.string(),
      description: z.string(),
      permissions: z.array(z.string()),
      details: z.array(
        z.object({
          title: z.string(),
          value: z.string(),
          url: z.optional(z.string()),
        })
      ),
      logo: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

const team = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/team" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string().optional(),
      bio: z.string().optional(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      socials: z
        .object({
          twitter: z.string().optional(),
          website: z.string().optional(),
          linkedin: z.string().optional(),
          email: z.string().optional(),
        })
        .optional(),
    }),
});

const postsCollection = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/posts" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.date(),
      description: z.string(),
      team: z.string(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

const customers = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/customers" }),
  schema: ({ image }) =>
    z.object({
      customer: z.string(),
      bgColor: z.string().optional(),
      ctaTitle: z.string().optional(),
      testimonial: z.string().optional(),
      partnership: z.string().optional(),
      avatar: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      challengesAndSolutions: z.array(
        z.object({
          title: z.string(),
          content: z.string(),
        })
      ),
      results: z.array(z.string()),
      about: z.string(),
      details: z.record(z.string(), z.string()),
      logo: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
    }),
});

export const collections = {
  team,
  customers,
  infopages,
  changelog,
  helpcenter,
  posts: postsCollection,
  integrations,
};
