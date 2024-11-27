"""
Collection of supporting functions using in the data preparation process.

@Author: Antonia Golab
@Dateofcreation: 2024-04-18

"""

"""
Check if a value exists in a DataFrame.

Args:
    df (DataFrame): The DataFrame to search in.
    column (Symbol): The column to search in.
    value (Any): The value to look for.

Returns:
    Bool: True if the value is found, False otherwise.
"""
function check_value(df::DataFrame, column::Symbol, value::Any)::Bool
    return any(df[!, column] .== value)
end

using DataFrames, XLSX

"""
Read an Excel file and define the attributes of a struct based on the values saved on one sheet.

Args:
    file_path (String): The path to the Excel file.
    sheet_name (String): The name of the sheet containing the attribute values.

Returns:
    DataFrame: The data read from the Excel file.
"""
function read_excel_and_define_struct(file_path::String, sheet_name::String)::DataFrame
    # Read the Excel file
    file = XLSX.readxlsx(file_path)
    sheet = file[sheet_name]

    # Get the attribute values from the sheet
    attribute_values = sheet.data[2:end, 1]

    # Define the column "module" with all indices
    df[!, :module] = 1:size(df, 1)

    # Read specific values from column "is_activated" using the indices
    is_activated_values = df[!, :is_activated][attribute_values]

    # Define the struct attributes based on the values
    struct_attributes = Symbol.(attribute_values)

    # Create an empty DataFrame with the struct attributes as columns
    df = DataFrame()
    for attribute ∈ struct_attributes
        df[!, attribute] = Any[]
    end

    return df
end
