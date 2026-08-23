import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const team = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/team" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string(),
      intro: z.string(),
      education: z.array(z.string()),
      experience: z.array(z.string()),
      avatar: z.object({
        url: image(),
        alt: z.string(),
      }),
    }),
});

const work = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/work" }),
  schema: ({ image }) =>
    z.object({
      link: z.string().optional(),
      company: z.string().optional(),
      year: z.string().optional(),
      client: z.string().optional(),
      work: z.string(),
      credits: z
        .array(
          z.object({
            name: z.string(),
            role: z.string(),
          })
        )
        .optional(),
      thumbnail: z.object({
        url: image(),
        alt: z.string(),
      }),
    }),
});

const services = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/services" }),
  schema: z.object({
    service: z.string(),
    description: z.string(),
  }),
});

const posts = defineCollection({
  loader: glob({ pattern: "**/*.(md|mdx)", base: "./src/content/posts" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.date(),
      description: z.string(),
      author: z.string(),
      image: z.object({
        url: image(),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.date(),
  }),
});

export const collections = {
  team,
  work,
  services,
  legal,
  posts,
};
