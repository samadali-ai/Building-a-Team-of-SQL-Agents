import streamlit as st
import pandas as pd
import sqlite3
import os
from pathlib import Path
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI
from crewai import Agent, Crew, Process, Task
from textwrap import dedent
from crewai_tools import tool
# Setup OpenAI and SQLDatabase
os.environ['GROQ_API_KEY'] = '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'

llm = ChatOpenAI(
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=os.environ['GROQ_API_KEY'],
    model_name="llama3-8b-8192",
    temperature=0,
    max_tokens=1000,
)

# Define database path
db_path = "salaries.db"

# Streamlit UI
st.title("CSV to SQLite and Agent Interaction")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    # Read CSV file
    df = pd.read_csv(uploaded_file)
    st.write("Data preview:")
    st.write(df.head())
    
    # Save DataFrame to SQLite
    with sqlite3.connect(db_path) as conn:
        df.to_sql(name="salaries", con=conn, if_exists='replace', index=False)
    
    # Initialize SQL Database
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    # Define tools
    @tool("list_tables")
    def list_tables() -> str:
        """List the available tables in the database."""
        return ListSQLDatabaseTool(db=db).invoke("")

    @tool("tables_schema")
    def tables_schema(tables: str) -> str:
        """
        Input is a comma-separated list of tables, output is the schema and sample rows
        for those tables. Be sure that the tables actually exist by calling `list_tables` first!
        Example Input: table1, table2, table3
        """
        tool = InfoSQLDatabaseTool(db=db)
        return tool.invoke(tables)

    @tool("execute_sql")
    def execute_sql(sql_query: str) -> str:
        """Execute a SQL query against the database. Returns the result."""
        return QuerySQLDataBaseTool(db=db).invoke(sql_query)

    @tool("check_sql")
    def check_sql(sql_query: str) -> str:
        """
        Use this tool to double check if your query is correct before executing it. Always use this
        tool before executing a query with `execute_sql`.
        """
        return QuerySQLCheckerTool(db=db, llm=llm).invoke({"query": sql_query})

    # Define agents and tasks
    sql_dev = Agent(
        role="Senior Database Developer",
        goal="Construct and execute SQL queries based on a request",
        backstory=dedent(
            """
            You are an experienced database engineer who is master at creating efficient and complex SQL queries.
            You have a deep understanding of how different databases work and how to optimize queries.
            Use the `list_tables` to find available tables.
            Use the `tables_schema` to understand the metadata for the tables.
            Use the `execute_sql` to check your queries for correctness.
            Use the `check_sql` to execute queries against the database.
            """
        ),
        llm=llm,
        tools=[list_tables, tables_schema, execute_sql, check_sql],
        allow_delegation=False,
    )

    data_analyst = Agent(
        role="Senior Data Analyst",
        goal="You receive data from the database developer and analyze it",
        backstory=dedent(
            """
            You have deep experience with analyzing datasets using Python.
            Your work is always based on the provided data and is clear,
            easy-to-understand and to the point. You have attention
            to detail and always produce very detailed work (as long as you need).
            """
        ),
        llm=llm,
        allow_delegation=False,
    )

    report_writer = Agent(
        role="Senior Report Editor",
        goal="Write an executive summary type of report based on the work of the analyst",
        backstory=dedent(
            """
            Your writing still is well known for clear and effective communication.
            You always summarize long texts into bullet points that contain the most
            important details.
            """
        ),
        llm=llm,
        allow_delegation=False,
    )

    extract_data = Task(
        description="Extract data that is required for the query {query}.",
        expected_output="Database result for the query",
        agent=sql_dev,
    )

    analyze_data = Task(
        description="Analyze the data from the database and write an analysis for {query}.",
        expected_output="Detailed analysis text",
        agent=data_analyst,
        context=[extract_data],
    )

    write_report = Task(
        description=dedent(
            """
            Write an executive summary of the report from the analysis. The report
            must be less than 100 words.
            """
        ),
        expected_output="Markdown report",
        agent=report_writer,
        context=[analyze_data],
    )

    crew = Crew(
        agents=[sql_dev, data_analyst, report_writer],
        tasks=[extract_data, analyze_data, write_report],
        process=Process.sequential,
        verbose=True,
        memory=False,
    )

    query = st.text_input("Enter your query:", "Effects on salary (in USD) based on company location, size and employee experience")

    if st.button("Run Query"):
        inputs = {"query": query}
        result = crew.kickoff(inputs=inputs)
        
        # Debugging: Inspect the result
        st.write("Debugging CrewOutput:")
        st.write(result)  # Inspect the entire result object

        # Example of how you might access attributes if available
        st.write("This project is done by : abdul samad a")
        if hasattr(result, 'extract_data'):
            st.write("7795738104")
            st.write(result.extract_data)
        else:
            st.write("7795738104")

        if hasattr(result, 'analyze_data'):
            st.write("Data Analyst Response:")
            st.write(result.analyze_data)
        else:
            st.write("samad.ali.hulikunte@gmail.com")

        if hasattr(result, 'write_report'):
            st.write("Report Writer Response:")
            st.write(result.write_report)
        else:
            st.write("This project involves creating a team of agents that can effectively answer complex questions by querying and analyzing data from a SQL database. The team will leverage CrewAI for SQL interactions and Llama 3 for sophisticated data analysis and reporting.")
