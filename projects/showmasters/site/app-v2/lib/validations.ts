/* Author: RKOJ-ELENO :: 2026-05-23
 * Zod schemas for every public-facing form. Used by both the client (rhf)
 * and the API route handler.
 */
import { z } from 'zod';

export const inquirySchema = z.object({
  name:    z.string().trim().min(2, 'Name is required').max(120),
  email:   z.string().trim().email('Valid email required').max(200),
  phone:   z.string().trim().max(50).optional().or(z.literal('')),
  company: z.string().trim().max(200).optional().or(z.literal('')),
  location: z.string().trim().max(200).optional().or(z.literal('')),
  dates:    z.string().trim().max(200).optional().or(z.literal('')),
  brief:    z.string().trim().min(20, 'Tell us a few sentences about the show').max(5000),
  source:   z.string().trim().max(60).optional().or(z.literal('')),
  turnstileToken: z.string().optional(),
});
export type InquiryInput = z.infer<typeof inquirySchema>;

export const applicationSchema = z.object({
  name:    z.string().trim().min(2).max(120),
  email:   z.string().trim().email().max(200),
  phone:   z.string().trim().max(50).optional().or(z.literal('')),
  city:    z.string().trim().max(120).optional().or(z.literal('')),
  state:   z.string().trim().max(40).optional().or(z.literal('')),
  role: z.enum([
    'STAGEHAND', 'RIGGER', 'TECHNICIAN', 'CAMERA_OP',
    'LIFT_OPERATOR', 'CREW_LEAD', 'SHOW_MANAGEMENT',
    'WAREHOUSE', 'DISPATCH', 'SALES', 'OTHER',
  ]),
  yearsExp: z.coerce.number().int().min(0).max(60).optional(),
  skills:   z.array(z.string().trim().max(60)).max(30).optional(),
  notes:    z.string().trim().max(5000).optional().or(z.literal('')),
  turnstileToken: z.string().optional(),
});
export type ApplicationInput = z.infer<typeof applicationSchema>;

export const newsletterSchema = z.object({
  email:  z.string().trim().email().max(200),
  source: z.string().trim().max(60).optional().or(z.literal('')),
});
export type NewsletterInput = z.infer<typeof newsletterSchema>;
