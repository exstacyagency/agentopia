// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore - adapter-pg types resolved at runtime
import pkg from "@prisma/adapter-pg";
const { PrismaPg } = pkg;
import { PrismaClient } from "../generated/prisma/client";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL ?? "" });
export const prisma = new PrismaClient({ adapter });
