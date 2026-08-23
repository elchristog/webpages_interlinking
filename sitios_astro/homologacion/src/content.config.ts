import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const infopages = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/infopages" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.coerce.date(),
  }),
});

const postsCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.coerce.date(),
      description: z.string(),
      image: z.object({
        url: image(),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

const speaker = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/speakers" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string().optional(),
      company: z.string().optional(),
      headshot: z
        .object({
          url: image(),
          alt: z.string().optional(),
        })
        .optional(),
      location: z.string().optional(),
      summary: z.string().optional(),
      tags: z.array(z.string()).optional(),
      socials: z
        .object({
          twitter: z.string().regex(/^(https?:\/\/|#_)/).optional(),
          github: z.string().regex(/^(https?:\/\/|#_)/).optional(),
          linkedin: z.string().regex(/^(https?:\/\/|#_)/).optional(),
          website: z.string().regex(/^(https?:\/\/|#_)/).optional(),
        })
        .optional(),
      talks: z.array(z.string()).optional(),
      featured: z.boolean().default(false),
    }),
});

const session = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/sessions" }),
  schema: z.object({
    title: z.string(),
    abstract: z.string().min(40),
    speakers: z.array(z.string()),
    day: z.enum(["day-1", "day-2", "day-3", "day-4", "day-5", "day-6", "day-7"]),
    start: z.string(),
    end: z.string(),
    room: z.string(),
    track: z.string().optional(),
    level: z.enum(["beginner", "intermediate", "advanced"]).optional(),
    tags: z.array(z.string()).default([]),
  }),
});

const sponsor = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/sponsors" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      tier: z.enum(["platinum", "gold", "silver", "bronze"]).default("bronze"),
      url: z.string().regex(/^(https?:\/\/|#_)/),
      logo: z.object({
        url: image(),
        alt: z.string().optional(),
      }),
    }),
});

export const collections = {
  infopages,
  posts: postsCollection,
  speakers: speaker,
  sessions: session,
  sponsors: sponsor,
};
