import { PrismaClient } from '@prisma/client';

// Global Prisma instance to avoid multiple connections
declare global {
  var __prisma: PrismaClient | undefined;
}

class PrismaService {
  private static instance: PrismaClient;
  
  static getInstance(): PrismaClient {
    if (!PrismaService.instance) {
      // Create a new Prisma client
      PrismaService.instance = globalThis.__prisma || new PrismaClient({
        log: process.env.NODE_ENV === 'development' ? ['error', 'warn'] : ['error'],
      });
      
      // Store in global to reuse
      if (!globalThis.__prisma) {
        globalThis.__prisma = PrismaService.instance;
      }
    }
    return PrismaService.instance;
  }
  
  static async disconnect(): Promise<void> {
    if (PrismaService.instance) {
      await PrismaService.instance.$disconnect();
      PrismaService.instance = null as any;
    }
    if (globalThis.__prisma) {
      await globalThis.__prisma.$disconnect();
      globalThis.__prisma = undefined;
    }
  }
  
  static async healthCheck(): Promise<boolean> {
    try {
      const prisma = PrismaService.getInstance();
      await prisma.$queryRaw`SELECT 1`;
      return true;
    } catch (error) {
      console.error('Prisma health check failed:', error);
      return false;
    }
  }
}

export default PrismaService;
export { PrismaClient };
export type { PrismaClient as PrismaClientType }; 