# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Entity relationship example generation module."""

import asyncio

from graphrag.language_model.protocol.base import ChatModel
from graphrag.prompt_tune.prompt.entity_relationship import (
    ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT,
    ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
    UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT,
)

MAX_EXAMPLES = 5


async def generate_entity_relationship_examples(
    model: ChatModel,
    persona: str,
    entity_types: str | list[str] | None,
    docs: str | list[str],
    language: str,
    json_mode: bool = False,
) -> list[str]:
    """Generate a list of entity/relationships examples for use in generating an entity configuration.

    Will return entity/relationships examples as either JSON or in tuple_delimiter format depending
    on the json_mode parameter.
    """
    docs_list = [docs] if isinstance(docs, str) else docs
    history = [{"content": persona, "role": "system"}]
    entity_str = """
        严格遵循定义的结构生成实体信息,确保将每个实体输出为单个元组结构,元组必须严格用括号 () 包裹,且成对匹配,不要生成多余},
        实体信息生成格式:("entity"{tuple_delimiter}实体名称{tuple_delimiter}实体类型{tuple_delimiter}实体描述)
        正确示例:("entity"{tuple_delimiter}ORGANIZATION{tuple_delimiter}organization{tuple_delimiter}组织部门实体，用于管理用户和权限，通过角色部门关联表与角色绑定")
        错误示例（确保避免）:
            括号不匹配,需要用括号 () 包裹内容变为了(}包裹:("entity"{tuple_delimiter}ROLE{tuple_delimiter}role{tuple_delimiter}系统中的角色，用于定义用户权限和访问控制，通过外键关联到菜单和部门"}
            括号缺失,需要用括号 () 包裹内容变为了只有(,缺少):("entity"{tuple_delimiter}MENU{tuple_delimiter}menu{tuple_delimiter}系统中的菜单项，用于导航和功能访问，通过角色菜单中间表与角色关联"
            多余},需要用括号 () 包裹内容变为了(})包裹:("entity"{tuple_delimiter}WECHAT_CONFIG{tuple_delimiter}organization{tuple_delimiter}微信配置信息表，用于存储微信相关系统配置参数的数据库表结构})
    """
    relationship_str = """
        严格遵循定义的结构生成响应，确保将每个关系输出为单个元组结构,元组必须严格用括号 () 包裹，且成对匹配,,不要生成多余}.
        关系信息生成格式:("relationship"{tuple_delimiter}来源实体{tuple_delimiter}目标实体{tuple_delimiter}关系描述{tuple_delimiter}关系强度数值)
        正确示例:("relationship"{tuple_delimiter}ROLE{tuple_delimiter}MENU{tuple_delimiter}角色通过role_menu表拥有菜单访问权限{tuple_delimiter}8)
        错误示例(确保避免):
            括号类型不匹配,需要用括号 () 包裹内容变为了(}包裹:("relationship"{tuple_delimiter}ROLE{tuple_delimiter}ORGANIZATION{tuple_delimiter}角色通过role_org表被分配到特定部门{tuple_delimiter}8}
            括号缺失,需要用括号 () 包裹内容变为了只有(,缺少):("relationship"{tuple_delimiter}ROLE_MENU{tuple_delimiter}MENU{tuple_delimiter}role_menu表中的menuId字段引用菜单表的id{tuple_delimiter}9
            多余},需要用括号 () 包裹内容变为了(})包裹:("relationship"{tuple_delimiter}WECHAT_CONFIG{tuple_delimiter}USER{tuple_delimiter}微信配置表可能包含用户权限配置信息{tuple_delimiter}3})
    """
    history.append({"content": entity_str,"role": "system"})
    history.append({"content": relationship_str,"role": "system"})

    if entity_types:
        entity_types_str = (
            entity_types
            if isinstance(entity_types, str)
            else ", ".join(map(str, entity_types))
        )

        messages = [
            (
                ENTITY_RELATIONSHIPS_GENERATION_JSON_PROMPT
                if json_mode
                else ENTITY_RELATIONSHIPS_GENERATION_PROMPT
            ).format(entity_types=entity_types_str, input_text=doc, language=language)
            for doc in docs_list
        ]
    else:
        messages = [
            UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT.format(
                input_text=doc, language=language
            )
            for doc in docs_list
        ]

    messages = messages[:MAX_EXAMPLES]

    tasks = [
        model.achat(message, history=history, json=json_mode) for message in messages
    ]

    responses = await asyncio.gather(*tasks)

    return [str(response.output.content) for response in responses]
