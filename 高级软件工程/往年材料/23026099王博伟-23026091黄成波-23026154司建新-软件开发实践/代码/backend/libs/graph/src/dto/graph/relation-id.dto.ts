import { ApiProperty } from '@nestjs/swagger'
import { IsEnum, IsInt } from 'class-validator'
import type { RelationType } from '../../schema'
import { RelationEnum } from '../../schema'
import { Type } from 'class-transformer'

export class RelationIdDto {
  @IsEnum(RelationEnum)
  @ApiProperty({ enum: RelationEnum })
  type: RelationType

  @IsInt()
  @Type(() => Number)
  from: number

  @IsInt()
  @Type(() => Number)
  to: number
}
