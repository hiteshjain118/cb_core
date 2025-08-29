import PrismaService from './client';

export interface Profile {
  id: bigint;
  timeZone: string | null;
  createdAt: Date;
  authUserId: string | null;
  firstName: string | null;
  lastName: string | null;
  email: string | null;
}

export class ProfileService {
  private static instance: ProfileService | null = null;

  private constructor() {
    // Private constructor to enforce singleton
  }

  // Singleton pattern to ensure only one instance
  public static getInstance(): ProfileService {
    if (!ProfileService.instance) {
      ProfileService.instance = new ProfileService();
    }
    return ProfileService.instance;
  }

  // Get or create a fresh Prisma client instance to avoid prepared statement conflicts
  private getPrismaClient() {
    return PrismaService.getInstance();
  }

  /**
   * Get user profile from the profiles table by cbid
   */
  async getUserProfile(cbid: bigint): Promise<Profile | null> {
    const prisma = this.getPrismaClient();
    try {
      const profile = await prisma.profile.findUnique({
        where: {
          id: cbid,
        },
      });

      if (!profile) {
        return null;
      }

      return profile;          
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Prisma query error: ${errorMessage}`, { error: String(error), cbid: cbid.toString() });
      
      throw error;
    }
  }

  /**
   * Get user profile from the profiles table by Supabase user ID
   */
  async getUserProfileBySupabaseUserId(supabaseUserId: string): Promise<{ cbid: bigint }> {
    try {
      const prisma = this.getPrismaClient();
      const profile = await prisma.profile.findFirst({
        where: {
          authUserId: supabaseUserId,
        },
      });

      if (!profile) {
        throw new Error(`No profile found for Supabase user ID: ${supabaseUserId}`);
      }

      return {
        cbid: profile.id,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Prisma query error: ${errorMessage}`, { error: String(error), supabaseUserId });
      
      throw error;
    }
  }

  /**
   * Get all profiles (for testing/debugging)
   */
  async getAllProfiles(): Promise<Profile[]> {
    try {
      const prisma = this.getPrismaClient();
      return await prisma.profile.findMany();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Prisma query error: ${errorMessage}`, { error: String(error) });
      throw error;
    }
  }

  /**
   * Create a new profile
   */
  async upsertProfile(data: {
    timeZone: string;
    authUserId: string;
    firstName: string;
    lastName: string;
    email: string;
  }): Promise<Profile> {
    const prisma = this.getPrismaClient();
    try {
      return await prisma.profile.upsert({
        where: {
          authUserId: data.authUserId,
        },
        update: {
          timeZone: data.timeZone,
          firstName: data.firstName,
          lastName: data.lastName,
          email: data.email,
        },
        create: {
          timeZone: data.timeZone,
          authUserId: data.authUserId,
          firstName: data.firstName,
          lastName: data.lastName,
          email: data.email,
        },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Prisma upsert error: ${errorMessage}`, { error: String(error), data });
      throw error;
    }
  }

  /**
   * Update an existing profile
   */
  async updateProfile(
    cbid: bigint,
    data: {
      timeZone?: string;
      authUserId?: string;
    }
  ): Promise<Profile | null> {
    try {
      const prisma = this.getPrismaClient();
      return await prisma.profile.update({
        where: { id: cbid },
        data,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Prisma update error: ${errorMessage}`, { error: String(error), cbid: cbid.toString(), data });
      throw error;
    }
  }
} 