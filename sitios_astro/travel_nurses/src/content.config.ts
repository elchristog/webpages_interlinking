import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const authors = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/authors" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string().optional(),
      bio: z.string().optional(),
      image: z.object({
        url: image(),
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

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.coerce.date(),
  }),
});

const podcast = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/podcast" }),
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
      guestAvatar: z.object({
        url: image(),
        alt: z.string(),
      }),
      episodeNumber: z.number().optional(),
      duration: z.string().optional(),
      audioSrc: z.string().optional(),
      tags: z.array(z.string()),
      isRecent: z.boolean().optional(),
      isPopular: z.boolean().optional(),
      isLocked: z.boolean().optional(),
    }),
});

const posts = defineCollection({
  loader: glob({
    pattern: "**/*.{md,mdx}",
    base: "./src/content/posts",
    retainBody: true,
  }),
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
      isRecent: z.boolean().optional(),
      isPopular: z.boolean().optional(),
      isLocked: z.boolean().optional(),
    }),
});

export const collections = {
  posts,
  authors,
  podcast,
  legal,
};
