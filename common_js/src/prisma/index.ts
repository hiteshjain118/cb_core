// Prisma client and service
export { default as PrismaService, PrismaClient } from './client';

// Profile service
export { ProfileService } from './profileService';
export type { Profile } from './profileService';

// Model event service
export { ModelEventService } from './modelEventService';
export type { ModelEvent } from './modelEventService';

// Task service
export { TaskService } from './taskService';
export type { Task, TaskWithDependencies } from './taskService';

// Re-export Prisma types for convenience - commented out until client is generated
// export type {
//   User,
//   QboProfile,
//   QboProfileSandbox,
//   Thread,
//   Message,
//   TableAttachment,
//   Pipeline,
// } from '@prisma/client'; 