import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db'
import { ActivityCategory, DifficultyLevel } from '@prisma/client'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const {
      title,
      description,
      category,
      difficulty,
      minDuration,
      maxDuration,
      typicalDuration,
      objectives,
      instructions,
      materials,
      tags,
      profession
    } = body

    // For now, we'll use a hardcoded user ID. In a real app, this would come from authentication
    const userId = "temp-user-id"

    const activity = await prisma.activity.create({
      data: {
        title,
        description,
        category: category as ActivityCategory,
        difficulty: difficulty as DifficultyLevel,
        minDuration: minDuration || typicalDuration - 10,
        maxDuration: maxDuration || typicalDuration + 15,
        typicalDuration,
        objectives: objectives || [],
        instructions: instructions || '',
        materials: materials || {},
        tags: tags || [],
        profession: profession || [],
        createdById: userId,
        isPublic: false,
        isArchived: false
      }
    })

    return NextResponse.json(activity)
  } catch (error) {
    console.error('Error creating activity:', error)
    return NextResponse.json(
      { error: 'Failed to create activity' },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    const activities = await prisma.activity.findMany({
      where: { isArchived: false },
      orderBy: { createdAt: 'desc' },
      take: 50
    })

    return NextResponse.json(activities)
  } catch (error) {
    console.error('Error fetching activities:', error)
    return NextResponse.json(
      { error: 'Failed to fetch activities' },
      { status: 500 }
    )
  }
}