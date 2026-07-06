import { IsEnum, IsInt } from 'class-validator'
import { Type } from 'class-transformer'
import { TreeEnum, TreeType } from '@app/graph/tree-schema'
import { ApiProperty } from '@nestjs/swagger'

export class TreeIdDto {
  @ApiProperty({ enum: TreeEnum })
  @IsEnum(TreeEnum)
  type: TreeType

  @IsInt()
  @Type(() => Number)
  id: number
}
