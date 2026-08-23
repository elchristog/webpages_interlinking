import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.coerce.date().optional(),
  }),
});

const authors = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/authors" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string().optional(),
      bio: z.string().optional(),
      image: z
        .object({
          url: image(),
          alt: z.string(),
        })
        .optional(),
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
      isBreaking: z.boolean().optional(),
      isTopStory: z.boolean().optional(),
      isFeatured: z.boolean().optional(),
      isBrief: z.boolean().optional(),
      isLocked: z.boolean().optional(),
    }),
});

const podcasts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/podcasts" }),
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
      episodeNumber: z.number().optional(),
      duration: z.string().optional(),
      audioSrc: z.string().optional(),
      tags: z.array(z.string()),
      isFeatured: z.boolean().optional(),
      isGuest: z.boolean().optional(),
      isSeries: z.boolean().optional(),
      isLocked: z.boolean().optional(),
    }),
});

const jobs = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/jobs" }),
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date().optional(),
    jobType: z.string().optional(),
    company: z.string().optional(),
    location: z.string().optional(),
    category: z.string().optional(),
    jobLevel: z.string().optional(),
    experience: z.string().optional(),
    salaryRange: z.string().optional(),
    description: z.string().optional(),
    benefits: z.array(z.string()).optional(),
    employmentStatus: z.string().optional(),
    requirements: z.array(z.string()).optional(),
    salaryType: z.string().optional(),
    referenceId: z.string().optional(),
    contactEmail: z.string().optional(),
    responsibilities: z.array(z.string()).optional(),
    hiringManager: z.string().optional(),
    companyCulture: z.string().optional(),
    perks: z.array(z.string()).optional(),
    skills: z.array(z.string()).optional(),
    workEnvironment: z.string().optional(),
    applicationDeadline: z.coerce.date().optional(),
    mediaLinks: z.array(z.string()).optional(),
    applicationInstructions: z.string().optional(),
  }),
});

const helpCenter = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/helpcenter" }),
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date().optional(),
    description: z.string().optional(),
  }),
});

export const collections = {
  authors,
  legal,
  posts,
  podcasts,
  jobs,
  helpCenter,
};
