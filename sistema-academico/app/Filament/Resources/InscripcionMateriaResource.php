<?php

namespace App\Filament\Resources;

use App\Filament\Resources\InscripcionMateriaResource\Pages;
use App\Models\InscripcionMateria;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class InscripcionMateriaResource extends Resource
{
    protected static ?string $model = InscripcionMateria::class;

    protected static ?string $navigationIcon = 'heroicon-o-rectangle-stack';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('matricula_id')
                    ->relationship('matricula', 'id')
                    ->required(),
                Forms\Components\Select::make('materia_id')
                    ->relationship('materia', 'id')
                    ->required(),
                Forms\Components\TextInput::make('origen')
                    ->required(),
                Forms\Components\TextInput::make('estado')
                    ->required(),
                Forms\Components\DatePicker::make('fecha_inscripcion')
                    ->required(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('matricula.id')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\TextColumn::make('materia.id')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\TextColumn::make('origen')
                    ->searchable(),
                Tables\Columns\TextColumn::make('estado')
                    ->searchable(),
                Tables\Columns\TextColumn::make('fecha_inscripcion')
                    ->date()
                    ->sortable(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                Tables\Columns\TextColumn::make('updated_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                //
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListInscripcionMaterias::route('/'),
            'create' => Pages\CreateInscripcionMateria::route('/create'),
            'edit' => Pages\EditInscripcionMateria::route('/{record}/edit'),
        ];
    }
}
